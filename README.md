# spikerc
Remote control of SPIKE Prime hub using Windows machine (that has bluetooth).

I started mentoring a FIRST Lego League (FLL) team a few weeks ago, we all (ok maybe mostly me) wanted to see remote control action. Here it is.

Demo vid: https://youtu.be/cMHl7u8XiDw

Use v2 of the Spike Prime app, not V3. V3 didn't have Python yet as of publishing this code.

"gamepad.py" will help you figure out how to get values from the controller.

"uart_example.py" is ripped from Bleak's examples, with a few mods. 

First, you run the robot code on the robot "robot_python_code.py". Just copy and paste it into Spike's Python editor, or you can use your more hipster dev env and push via Ampy, up to you. Then, you run "uart_example.py" on your Windows machine to connect to the robot. Then you have fun.

I didn't do anything novel here, just piecing together stuff from here and there. :)

Enjoy!
