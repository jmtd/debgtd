PREFIX=/usr/local
BINDIR=$(PREFIX)/bin
SHAREDIR=$(PREFIX)/share
LIBDIR=$(PREFIX)/lib/python2.5/site-packages
MANDIR=$(PREFIX)/share/man

DESTDIR=

help:
	printf "make install\t\tinstall the tool\n"

install:
	install -D -m 0755 debgtd.py $(DESTDIR)$(BINDIR)/debgtd
	install -D -m 0644 debgtd.glade $(DESTDIR)$(SHAREDIR)/debgtd/debgtd.glade
	install -D -m 0644 debgtd/controller.py $(DESTDIR)$(LIBDIR)/debgtd/controller.py
	install -D -m 0644 debgtd/model.py $(DESTDIR)$(LIBDIR)/debgtd/model.py
	install -D -m 0644 debgtd/gui.py $(DESTDIR)$(LIBDIR)/debgtd/gui.py
	install -D -m 0644 debgtd/__init__.py $(DESTDIR)$(LIBDIR)/debgtd/__init__.py
	install -D -m 0644 debgtd.1 $(DESTDIR)$(MANDIR)/man1/debgtd.1

clean:
	rm -f *.pyc debgtd/*.pyc

FILES=$(DESTDIR)$(BINDIR)/debgtd \
		$(DESTDIR)$(SHAREDIR)/debgtd/debgtd.glade \
		$(DESTDIR)$(LIBDIR)/debgtd/model.py \
		$(DESTDIR)$(LIBDIR)/debgtd/controller.py \
		$(DESTDIR)$(LIBDIR)/debgtd/gui.py \
		$(DESTDIR)$(LIBDIR)/debgtd/__init__.py \
		$(DESTDIR)$(MANDIR)/man1/debgtd.1

list:
	ls -dl $(FILES)

uninstall:
	rm -f $(FILES)

.PHONY: default install list uninstall
