Opartrac: Open-format particle tracking
===

Scratchbook
----

I am in major need of some threading, because this shit is just all wrong.

General Notes
---

Hello world!

Technical Notes
====

Architecture
---

Gui functions are in gui.py
Implement control via methods for extension of app in main.py
Methods of Opartrac class in main.py function as interfaces between the gui and the outside world, such that either can change independently and the only modifications needed will be within main.py
