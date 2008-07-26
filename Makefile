PREFIX=/usr/local
BINDIR=$(PREFIX)/bin
SHAREDIR=$(PREFIX)/share
LIBDIR=$(PREFIX)/lib/python2.5/site-packages
MANDIR=$(PREFIX)/share/man
DESKTOPDIR=$(PREFIX)/share/applications

DESTDIR=

help:
	printf "make install\t\tinstall the tool\n"

debgtd.desktop: debgtd.desktop.in
	m4 -DPREFIX=$(BINDIR) < $< > $@

install:
	install -D -m 0755 debgtd.py $(DESTDIR)$(BINDIR)/debgtd
	install -D -m 0644 debgtd.glade $(DESTDIR)$(SHAREDIR)/debgtd/debgtd.glade
	install -D -m 0644 debgtd/controller.py $(DESTDIR)$(LIBDIR)/debgtd/controller.py
	install -D -m 0644 debgtd/model.py $(DESTDIR)$(LIBDIR)/debgtd/model.py
	install -D -m 0644 debgtd/gui.py $(DESTDIR)$(LIBDIR)/debgtd/gui.py
	install -D -m 0644 debgtd/__init__.py $(DESTDIR)$(LIBDIR)/debgtd/__init__.py
	install -D -m 0644 debgtd.1 $(DESTDIR)$(MANDIR)/man1/debgtd.1
	install -D -m 0644 debgtd.desktop $(DESTDIR)$(DESKTOPDIR)/debgtd.desktop

clean:
	rm -f *.pyc debgtd/*.pyc
	rm debgtd.desktop

FILES=$(DESTDIR)$(BINDIR)/debgtd \
		$(DESTDIR)$(SHAREDIR)/debgtd/debgtd.glade \
		$(DESTDIR)$(LIBDIR)/debgtd/model.py \
		$(DESTDIR)$(LIBDIR)/debgtd/controller.py \
		$(DESTDIR)$(LIBDIR)/debgtd/gui.py \
		$(DESTDIR)$(LIBDIR)/debgtd/__init__.py \
		$(DESTDIR)$(MANDIR)/man1/debgtd.1 \
		$(DESTDIR)$(DESKTOPDIR)/debgtd.desktop

list:
	ls -dl $(FILES)

uninstall:
	rm -f $(FILES)

.PHONY: default install list uninstall
