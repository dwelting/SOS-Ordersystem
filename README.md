
# SOS, a Simple Order System.

A multifunctional database manager using sqlite3.

This is something I made to keep track of all the ordering I do for my job. The idea is that there is a shared database on a network drive, and colleagues can use this program to add the items they want to that database. The person actually doing the ordering (using admin mode) can then see which orders have to be purchased. It will also keep a record of past purchases, returns, etc. If you provide a URL with the order the program can later open these for easy review.

It also has a button to automatically import item data from the Farnell website using the items ordercode or URL. Although this can regularly break when they update their website.

Optimization has been a big part of the devolvement, so it can easily handle databases with thousands of items.

---

An installer script is included. This will install the program on a Windows pc to the Appdata folder.

---

Someday™ I will refactor this code into something pretty. For now this is useful as a starting point for your own database manager, or for code examples of python sqlite3 and Qt tables. Although it is fully functional.
