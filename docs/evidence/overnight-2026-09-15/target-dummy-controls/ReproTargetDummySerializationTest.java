import arc.util.io.*;
import mindustry.content.*;
import mindustry.game.*;
import mindustry.world.blocks.defense.TargetDummy;
import mindustry.world.blocks.defense.TargetDummy.TargetDummyBuild;
import org.junit.jupiter.api.*;
import org.junit.jupiter.params.*;
import org.junit.jupiter.params.provider.*;
import java.io.*;
import static org.junit.jupiter.api.Assertions.*;

public class ReproTargetDummySerializationTest{
    @BeforeAll
    public static void setup(){ ApplicationTests.launchApplication(); }

    private TargetDummyBuild fresh(Team buildingTeam){
        TargetDummyBuild build = ((TargetDummy)Blocks.targetDummy).new TargetDummyBuild();
        build.team = buildingTeam;
        build.boosting = true;
        build.unitArmor = 17f;
        build.resetTime = 90f;
        build.dummySize = 16f;
        return build;
    }

    private void roundTrip(TargetDummyBuild source, Team expectedTeam) throws IOException{
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        source.write(new Writes(new DataOutputStream(bytes)));
        assertEquals(21, bytes.size(), "Existing serialization layout must be retained");
        TargetDummyBuild loaded = fresh(source.team);
        loaded.read(new Reads(new DataInputStream(new ByteArrayInputStream(bytes.toByteArray()))), (byte)0);
        assertEquals(expectedTeam, loaded.unitTeam);
        assertEquals(-1, loaded.readUnitId);
        assertTrue(loaded.boosting);
        assertEquals(17f, loaded.unitArmor);
        assertEquals(90f, loaded.resetTime);
        assertEquals(16f, loaded.dummySize);
    }

    @ParameterizedTest
    @ValueSource(ints = {0, 1, 2})
    public void defaultTeamSavesBeforeFirstUpdate(int id) throws IOException{
        Team team = Team.get(id);
        TargetDummyBuild source = fresh(team);
        assertNull(source.unitTeam, "This regression must exercise the uninitialized value");
        roundTrip(source, team);
    }

    @Test
    public void explicitTeamIsPreserved() throws IOException{
        TargetDummyBuild source = fresh(Team.sharded);
        source.unitTeam = Team.crux;
        roundTrip(source, Team.crux);
    }
}
