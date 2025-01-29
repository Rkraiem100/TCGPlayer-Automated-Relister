# TCGPlayer-Automated-Relister
=======================================================================================================================================================================================================================================================================================================
***IMPORTANT NOTE!!!*** This program makes use of a command and control server and arbitrary code execution through polymorphic payloads. This can be viewed as a very serious security risk for any machine you run the worker on. It is strongly advised that you use a dedicated virtual machine on a separate vlan from anything separate. The code is designed to only work over a local network but the nature of arbitrary code execution means it can be easily abused for malicious ends if a 3rd party gains access to your network.

As for why I would code the program to work this way... Well I'm a network admin not a programmer. Separating out a VLAN and setting up a VM is much easier for me than figuring out how to do this in a way that isn't a massive security risk. 

I am not responsible for any damage you do to your own machine using this code, nor how anybody choses to modify it. This code is designed for legitimate purposes of automation of local self-hosted VMs.
=======================================================================================================================================================================================================================================================================================================
How to set up the program:

This program consists of a command and control server (C&C) along with a worker executable.

What you need:

1- A computer to act as a server (any computer will do)

2- A 2nd computer or a virtual machine (virtual machine is strongly recommended). For security reasons it MUST be a system not used for other purposes.

3- A TCGPlayer store account. You do not need pro, it will work with any level store

Initial setup:

1- Set up the VM. It is strongly recommended that during setup, you boot into a recovery ISO such as hiren boot cd and delete windows defender. Google how to do that I don't remember what folder is safe to delete and I don't want to be responsible for any bricked PCs. This is an important step since the program sends arbitrary code over the local network and during testing, it appears that even with windows defender turned off, it was blocking the commands without leaving a notification that it did so. This is why its recommended to use a VM as well.

2- Set up the environment. You're gonna need to install a lot of pips. I will prob write up a list of them or maybe just make a .bat to install them all later.

3- Create a folder called "WorkerImages" in the root C directory. Download the images and put them in that folder. This allows the program to know how to navigate.

4- Modify the server side code in cc.py if I recall correctly to put your own email API info. The program scans for sales of specific cards you whitelist elsewhere, it waits for a gmail or other api email saying a card sold and then sends a command to the worker to relist it under preset parameters.

5- Download the Brave browser. If you want to use another browser you can, just modify the code appropriately. Also make sure to sign in and save the credentials so the program can use them as needed. NOTE!!! This program DOES NOT collect any credentials, nor does it transmit any information over the internet! It relies entirely on the credentials cached in your browser for security purposes.

6- Modify the code to add in any cards you want relisted on sale and make sure to include direct links to the relist page.

7- Run the server side code and make sure the server checkbox is on and the relister checkbox is also on.

8- Run the worker code.

9- When a sale comes in, it should hijack the mouse and keyboard of the virtual machine in order to navigate to the web page of the item listing and relist it according to your parameters.

And thats it. 9 not so easy steps.

I will be pushing updates over time to make this as secure as I can, add features, and fix bugs.
