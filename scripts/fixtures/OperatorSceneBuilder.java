import arc.*;
import arc.backend.headless.*;
import arc.files.*;
import arc.struct.*;
import arc.util.*;
import mindustry.*;
import mindustry.content.*;
import mindustry.core.*;
import mindustry.game.*;
import mindustry.gen.*;
import mindustry.io.*;
import mindustry.mod.*;
import mindustry.net.*;
import mindustry.world.*;

import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

import static mindustry.Vars.*;

/** Operator-authored precondition scenes. No symptom, candidate or future source is encoded. */
public class OperatorSceneBuilder{
    public static void main(String[] args){
        try{
            run(args);
        }catch(Throwable failure){
            failure.printStackTrace();
            System.exit(1);
        }
    }

    public static void run(String[] args) throws Exception{
        String mode = args[0];
        Fi output = new Fi(args[1]);
        output.mkdirs();
        CountDownLatch initialized = new CountDownLatch(1);
        AtomicReference<Throwable> failure = new AtomicReference<>();
        Log.useColors = false;
        new HeadlessApplication(new ApplicationCore(){
            @Override
            public void setup(){
                Core.settings.setDataDirectory(new Fi("/work/profile"));
                headless = true;
                net = new Net(null);
                tree = new FileTree();
                Vars.init();
                world = new World();
                content.createBaseContent();
                content.createModContent();
                add(logic = new Logic());
                add(netServer = new NetServer());
                content.init();
            }

            @Override
            public void init(){
                super.init();
                initialized.countDown();
                // Keep the simulation thread parked while main constructs and serializes the scene.
                try{
                    new CountDownLatch(1).await();
                }catch(InterruptedException error){
                    throw new RuntimeException(error);
                }
            }
        }, error -> {failure.set(error); initialized.countDown();});
        if(!initialized.await(30, TimeUnit.SECONDS)) throw new IllegalStateException("Initialization timed out");
        if(failure.get() != null) throw new IllegalStateException("Initialization failed", failure.get());
        Time.setDeltaProvider(() -> 1f);
        logic.reset();
        state.rules = Gamemode.sandbox.apply(new Rules());
        state.rules.editor = false;
        state.rules.reactorExplosions = true;
        state.rules.waveTimer = false;
        state.rules.defaultTeam = Team.sharded;
        state.rules.fog = false;
        state.rules.staticFog = false;
        String name = "REPRO prepared " + mode + " scene";
        Fi file = output.child("operator-" + mode + "-setup.msav");
        state.map = new mindustry.maps.Map(file, 160, 120, StringMap.of(
            "name", name,
            "author", "REPRO operator setup",
            "description", "Prepared healthy preconditions only. Not an original reporter attachment or a reproduction result."
        ), true);
        world.beginMapLoad();
        Tiles tiles = world.resize(160, 120);
        for(int x = 0; x < tiles.width; x++){
            for(int y = 0; y < tiles.height; y++){
                tiles.set(x, y, new Tile(x, y, Blocks.stone, Blocks.air, Blocks.air));
            }
        }
        tiles.getn(68, 60).setBlock(Blocks.coreShard, Team.sharded);
        if(mode.equals("generator")){
            tiles.getn(84, 60).setBlock(Blocks.steamGenerator, Team.sharded);
            tiles.getn(83, 60).setBlock(Blocks.liquidSource, Team.sharded);
            tiles.getn(86, 60).setBlock(Blocks.itemSource, Team.sharded);
            tiles.getn(96, 60).setBlock(Blocks.payloadConveyor, Team.sharded, 0);
        }else if(mode.equals("unit")){
            tiles.getn(90, 60).setBlock(Blocks.payloadConveyor, Team.sharded, 0);
            tiles.getn(93, 60).setBlock(Blocks.payloadConveyor, Team.sharded, 0);
            tiles.getn(96, 60).setBlock(Blocks.payloadConveyor, Team.sharded, 0);
        }else{
            throw new IllegalArgumentException("Unknown scene " + mode);
        }
        world.endMapLoad();
        if(mode.equals("generator")){
            tiles.getn(83, 60).build.configured(null, Liquids.water);
            // Exercise normal source delivery while the generator remains unfueled.
            for(int tick = 0; tick < 120; tick++){
                tiles.getn(83, 60).build.update();
                tiles.getn(84, 60).build.update();
            }
            Unit unit = UnitTypes.mega.create(Team.sharded);
            unit.set(82 * tilesize, 56 * tilesize);
            unit.add();
        }else{
            for(int y : new int[]{56, 60, 64}){
                Unit unit = UnitTypes.dagger.create(Team.sharded);
                unit.set(84 * tilesize, y * tilesize);
                unit.add();
            }
        }
        player = Player.create();
        player.team(Team.sharded);
        player.set(86 * tilesize, 60 * tilesize);
        state.set(GameState.State.paused);
        check(mode);
        SaveIO.write(file);
        logic.reset();
        SaveIO.load(file);
        check(mode);
        String audit = "{\"mode\":\"" + mode + "\",\"operator_prepared\":true," +
            "\"save_reload_preconditions_pass\":true,\"editor\":" + state.rules.editor +
            ",\"infinite_resources\":" + state.rules.infiniteResources +
            ",\"reactor_explosions\":" + state.rules.reactorExplosions +
            ",\"unit_count\":" + Groups.unit.size() +
            ",\"fixture_bytes\":" + file.length() +
            ",\"symptom_tested\":false,\"file\":\"" + file.name() + "\"}\n";
        output.child(mode + "-setup-audit.json").writeString(audit);
        System.out.print(audit);
        System.exit(0);
    }

    static void require(boolean value, String message){
        if(!value) throw new IllegalStateException(message);
    }

    static void check(String mode){
        require(!state.rules.editor && state.rules.infiniteResources, "Must use normal sandbox rules, not editor mode");
        require(state.rules.reactorExplosions, "Reactor explosions must be enabled");
        require(Team.sharded.core() != null, "Friendly core missing");
        if(mode.equals("generator")){
            Building generator = world.build(84, 60);
            require(generator != null && generator.block == Blocks.steamGenerator, "Steam generator missing");
            require(generator.health == generator.maxHealth && generator.health > 0, "Generator must start healthy");
            require(generator.items.total() == 0, "Generator must start unfueled; AI must perform fueling");
            require(world.build(86, 60).config() == null, "Item source must start unconfigured");
            require(world.build(83, 60).config() == Liquids.water, "Water source configuration missing");
            require(generator.liquids.get(Liquids.water) > 0, "Normal water delivery did not reach generator");
            require(world.build(96, 60).getPayload() == null, "Conveyor must start empty");
            require(Groups.unit.count(u -> u.type == UnitTypes.mega && u.team == Team.sharded && u.health > 0) == 1, "Healthy Mega missing");
        }else{
            require(Groups.unit.count(u -> u.type == UnitTypes.dagger && u.team == Team.sharded && u.health > 0) == 3, "Three healthy ground units required");
            for(int x : new int[]{90, 93, 96}) require(world.build(x, 60).getPayload() == null, "Conveyors must start empty");
        }
    }
}
