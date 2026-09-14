import arc.*;
import arc.backend.sdl.*;
import arc.input.*;
import java.nio.file.*;
public class ArcWheelProbe implements ApplicationListener {
    int frame; int received; int previous; long started; int sleep;
    public ArcWheelProbe(int sleep){this.sleep=sleep;}
    public void init(){
        started=System.nanoTime();
        Core.input.addProcessor(new InputProcessor(){public boolean scrolled(float x,float y){received++;return false;}});
        try{java.nio.file.Files.writeString(Path.of("/workspace/runtime/probe-ready"),"ready");}catch(Exception e){throw new RuntimeException(e);}
    }
    public void update(){
        frame++;
        float axis=Core.input.axis(KeyCode.scroll);
        if(axis!=0 || received!=previous){
            System.out.println("{\"frame\":"+frame+",\"axis\":"+axis+",\"wheel_events\":"+(received-previous)+"}");
            System.out.flush(); previous=received;
        }
        Core.graphics.clear(0.15f,0.15f,0.15f,1f);
        if(System.nanoTime()-started>30_000_000_000L)Core.app.exit();
        try{Thread.sleep(sleep);}catch(Exception e){throw new RuntimeException(e);}
    }
    public static void main(String[] args){
        SdlConfig c=new SdlConfig();c.title="REPRO wheel delivery probe";c.width=640;c.height=480;
        new SdlApplication(new ArcWheelProbe(Integer.parseInt(args[0])),c);
    }
}
