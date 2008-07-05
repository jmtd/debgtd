DESTDIR=
PREFIX=/usr/local
BINDIR=$(DESTDIR)$(PREFIX)/bin
SHAREDIR=$(DESTDIR)$(PREFIX)/share
LIBDIR=$(DESTDIR)$(PREFIX)/lib/python2.5/site-packages
MANDIR=$(DESTDIR)$(PREFIX)/share/man

default:
	echo $(PREFIX)

install:
	install -D -m 0755 btsgui.py $(BINDIR)/debgtd
	install -D -m 0644 bts.glade $(SHAREDIR)/debgtd/bts.glade
	install -D -m 0644 bts.py $(LIBDIR)/bts.py
	install -D -m 0644 debgtd.1 $(MANDIR)/man1/debgtd.1

FILES=$(BINDIR)/debgtd \
		$(SHAREDIR)/debgtd/bts.glade \
		$(LIBDIR)/bts.py \
		$(MANDIR)/man1/debgtd.1

list:
	ls -dl $(FILES)

uninstall:
	rm -f $(FILES)

.PHONY: default install list uninstall
