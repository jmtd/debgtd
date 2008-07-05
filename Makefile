PREFIX=/usr/local
BINDIR=$(PREFIX)/bin
SHAREDIR=$(PREFIX)/share
LIBDIR=$(PREFIX)/lib/python2.5

DESTDIR=

default:
	echo $(PREFIX)

install:
	install -D -m 0755 btsgui.py $(DESTDIR)/$(BINDIR)/debgtd
	install -D -m 0644 bts.glade $(DESTDIR)/$(SHAREDIR)/debgtd/bts.glade
	install -D -m 0644 bts.py $(DESTDIR)/$(LIBDIR)/bts.py

.PHONY: default install
