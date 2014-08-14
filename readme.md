Opartrac: Open-format particle tracking
===

Scratchbook
----

Should probably rewrite phz to use the coordinated df from phn. Then will need to add a bit in the gui for selecting which fields are the coordinates. Should I combine phz and phn? What use is the one without the other?

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
