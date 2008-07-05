PREFIX=/usr/local
BINDIR=$(PREFIX)/bin
SHAREDIR=$(PREFIX)/share

DESTDIR=

default:
	echo $(PREFIX)

install:
	install -D -m 0755 btsgui.py $(DESTDIR)/$(BINDIR)/debgtd
	install -D -m 0644 bts.glade $(DESTDIR)/$(SHAREDIR)/debgtd/bts.glade

.PHONY: default install
