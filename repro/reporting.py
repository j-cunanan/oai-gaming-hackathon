"""A plain, printable report assembled from saved case evidence, without model calls."""

from datetime import UTC, datetime
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from PIL import Image as PillowImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from repro.models import Case, patch_validated
from repro.storage.store import Store

INK = colors.HexColor("#20252C")
MUTED = colors.HexColor("#626A73")
RULE = colors.HexColor("#DADEE3")
WIDTH = A4[0] - 88


@lru_cache(maxsize=1)
def register_fonts():
    # These redistributable fonts ship with ReportLab; no host font dependency.
    fonts = Path(reportlab.__file__).parent / "fonts"
    for name, filename in (("Repro", "Vera.ttf"), ("Repro-Bold", "VeraBd.ttf")):
        pdfmetrics.registerFont(TTFont(name, fonts / filename))
    pdfmetrics.registerFontFamily("Repro", normal="Repro", bold="Repro-Bold")


def plain(text: str) -> str:
    return text.translate(str.maketrans({"\u2011": "-", "\u2013": "-", "\u2014": "-"}))


def render_report(case: Case, store: Store) -> bytes:
    register_fonts()
    body = ParagraphStyle(
        "body", fontName="Repro", fontSize=9, leading=13.5, textColor=INK, spaceAfter=7
    )
    small = ParagraphStyle("small", parent=body, fontSize=7.7, leading=11, textColor=MUTED)
    heading = ParagraphStyle(
        "heading",
        parent=body,
        fontName="Repro-Bold",
        fontSize=11,
        leading=15,
        spaceBefore=15,
        spaceAfter=7,
        keepWithNext=True,
    )
    title = ParagraphStyle(
        "title", parent=heading, fontSize=24, leading=29, spaceBefore=0, spaceAfter=8
    )
    code_style = ParagraphStyle(
        "code",
        fontName="Courier",
        fontSize=7,
        leading=10,
        textColor=INK,
        backColor=colors.HexColor("#F4F5F7"),
        borderPadding=7,
        spaceAfter=8,
    )

    def p(text, style=body):
        # Case text is data, never ReportLab markup or a link destination.
        return Paragraph(escape(plain(str(text))).replace("\n", "<br/>"), style)

    story = [p("REPRO Report", title), p(case.report.title, heading)]
    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    state = case.state.replace("_", " ").capitalize()
    story += [
        p(f"Case {case.id}  |  {case.report.game.capitalize()}  |  {state}", small),
        p(f"Revision: {case.report.target_commit}", small),
        p(
            f"Reported platform: {case.report.platform}  |  Build: {case.report.build_version or 'Unspecified'}",
            small,
        ),
        p(f"Generated {generated} from the current saved case.", small),
        Spacer(1, 4),
        p(case.summary),
    ]
    rep = case.reproduction
    proof = case.first_reproduced_seconds
    stats = Table(
        [
            [
                p(label, small)
                for label in ("Reproduction", "Time to first proof", "Replay actions")
            ],
            [
                p(value)
                for value in (
                    f"{rep.successful_runs}/{rep.total_runs} clean runs" if rep else "Not measured",
                    f"{int(proof) // 60}:{int(proof) % 60:02d}"
                    if proof is not None
                    else "Not measured",
                    f"{rep.original_actions} to {len(rep.steps)}" if rep else "Not recorded",
                )
            ],
        ],
        colWidths=[WIDTH / 3] * 3,
        hAlign="LEFT",
    )
    stats.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F6F8")),
                ("BOX", (0, 0), (-1, -1), 0.5, RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
            ]
        )
    )
    story += [stats, p("Player report", heading), p(case.report.body)]
    if case.spec:
        if case.spec.expected_behavior:
            story += [p("Expected behavior: " + case.spec.expected_behavior)]
        if case.spec.uncertain_conditions:
            story += [
                p("Initial questions", heading),
                p(
                    "Recorded at intake; later findings and validation may address these questions.",
                    small,
                ),
            ]
            story += [p("- " + question) for question in case.spec.uncertain_conditions]

    if rep:
        story += [p("Recorded reproduction", heading)]
        for i, action in enumerate(rep.steps, 1):
            story.append(p(f"{i}. {action.semantic or action.action}"))
        story += [
            p(
                "Each replay starts with a fresh profile. Reproduction counts describe this case; "
                "action reduction is bounded and is not proof of a globally minimal replay.",
                small,
            )
        ]

    if case.findings:
        story += [p("Source diagnosis", heading), p(case.findings.root_cause)]
        for candidate in case.findings.candidates:
            story += [p(candidate.path, small), p(candidate.reasoning)]

    if case.patch_artifact:
        story += [p("Proposed patch", heading)]
        if case.patch_rationale:
            story += [p("Why this patch should work", heading), p(case.patch_rationale.explanation)]
            story += [p("Risks and tradeoffs", heading)]
            story += [p("- " + risk) for risk in case.patch_rationale.risks] or [
                p("No specific risks were recorded. Human review is still required.")
            ]
        else:
            story += [p("No saved explanation is available for this patch.")]
        try:
            path, _ = store.artifact_path(case.id, case.patch_artifact)
            diff = path.read_text(errors="replace")
        except (KeyError, OSError):
            story += [p("The patch file is unavailable in this workspace.", small)]
        else:
            story += [
                p("Code changes", heading),
                p(
                    "Lines starting with - are removed; lines starting with + are added. Unmarked lines provide context.",
                    small,
                ),
            ]
            # Plain preformatted text avoids interpreting code as markup.
            story += [Preformatted(plain(diff), code_style, maxLineLength=106)]

    validation = [p("Validation results", heading)]
    validation += [
        p(
            "All five required checks passed. Approval is a separate human review decision."
            if patch_validated(case)
            else "Validation is incomplete or has failed. The recorded results below determine what has been verified."
        )
    ]
    if case.checks:
        rows = [[p("Check", small), p("Result", small), p("Recorded evidence", small)]]
        rows += [
            [p(c.name), p(c.status.replace("_", " ").upper()), p(c.detail)] for c in case.checks
        ]
        table = Table(rows, colWidths=[138, 59, WIDTH - 197], repeatRows=1, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F0F2F4")),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, RULE),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        validation.append(table)
    else:
        validation.append(p("No validation checks have been recorded yet."))
    story.append(KeepTogether(validation))
    if case.findings and case.findings.limitations:
        story += [p("Limitations", heading)]
        story += [p("- " + limit) for limit in case.findings.limitations]
    story += [
        p("Usage and review", heading),
        p(
            f"{case.usage.model_calls:,} model calls; {case.usage.input_tokens:,} input tokens; "
            f"{case.usage.output_tokens:,} output tokens. Usage accumulates across jobs on this case. "
            "PDF export uses saved data and makes no model calls.",
            small,
        ),
        p(
            "The proposed patch lives in a disposable game workspace. Handoff approval records a local "
            "review decision and does not publish or merge changes upstream. Visual checks are model-based; "
            "startup smoke does not establish broad gameplay coverage.",
            small,
        ),
    ]

    screenshots = []
    if rep and rep.evidence:
        screenshots.append(("Baseline replay evidence", rep.evidence[-1]))
    if case.latest_screenshot and case.latest_screenshot not in {a for _, a in screenshots}:
        screenshots.append(("Latest recorded game screen", case.latest_screenshot))
    if screenshots:
        story += [PageBreak(), p("Recorded screenshots", heading)]
        for label, artifact_id in screenshots:
            try:
                path, media_type = store.artifact_path(case.id, artifact_id)
                if media_type not in {"image/png", "image/jpeg"}:
                    raise ValueError("Not a captured image")
                with PillowImage.open(path) as img:
                    width, height = img.size
                scale = min(WIDTH / width, 266 / height)
                figure = Image(str(path), width=width * scale, height=height * scale, hAlign="LEFT")
                story.append(
                    KeepTogether([p(label, heading), figure, Spacer(1, 5), p(artifact_id, small)])
                )
            except (KeyError, OSError, ValueError):
                story.append(p(f"{label}: screenshot unavailable in this workspace.", small))

    output = BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=44,
        rightMargin=44,
        topMargin=44,
        bottomMargin=44,
        title="REPRO Report",
        author="REPRO",
        subject=case.report.title,
        pageCompression=1,
    )

    def footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(RULE)
        canvas.line(44, 33, A4[0] - 44, 33)
        canvas.setFont("Repro", 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(44, 21, "REPRO Report | " + case.id[:40])
        canvas.drawRightString(A4[0] - 44, 21, f"Page {document.page}")
        if document.page > 1:
            canvas.drawString(44, A4[1] - 28, "REPRO Report")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
