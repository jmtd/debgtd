PREFIX=/usr/local
BINDIR=$(PREFIX)/bin
SHAREDIR=$(PREFIX)/share
LIBDIR=$(PREFIX)/lib/python2.5/site-packages
MANDIR=$(PREFIX)/share/man

DESTDIR=

default:
	echo $(PREFIX)

install:
	install -D -m 0755 btsgui.py $(DESTDIR)$(BINDIR)/debgtd
	install -D -m 0644 bts.glade $(DESTDIR)$(SHAREDIR)/debgtd/bts.glade
	install -D -m 0644 bts.py $(DESTDIR)$(LIBDIR)/bts.py
	install -D -m 0644 debgtd.1 $(DESTDIR)$(MANDIR)/man1/debgtd.1

FILES=$(DESTDIR)$(BINDIR)/debgtd \
		$(DESTDIR)$(SHAREDIR)/debgtd/bts.glade \
		$(DESTDIR)$(LIBDIR)/bts.py \
		$(DESTDIR)$(MANDIR)/man1/debgtd.1

list:
	ls -dl $(FILES)

uninstall:
	rm -f $(FILES)

.PHONY: default install list uninstall
