# oui

Which organization a MAC address belongs to, as small static files on GitHub
Pages, rebuilt weekly from the IEEE Registration Authority's public registries
(MA-L, MA-M and MA-S).

A lookup fetches one file for the MAC's first four hex digits, and a second
for its first seven when that base is split into 36-bit assignments, then
takes the longest prefix that matches. Nothing else about the MAC is sent.
A locally administered address (bit 0x02 of the first byte, as most phones and
laptops use now) has no vendor and needs no fetch. `lookup.mjs` is the
reference; `build.py` makes the files.

    https://oss.pulzr.net/oui/v1/meta.json
    https://oss.pulzr.net/oui/v1/3C5A.json

The data is the IEEE's; this repository only reshapes it.
