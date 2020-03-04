RPMLOC = $(shell find cache -type f -name *.rpm)
$(info RPMLOC is $(RPMLOC))
$(info PATH is $(shell pwd))
$(info contents is $(shell find))
localrepo:
	$(info making localrepo in $(CURDIR))
	mkdir -p $(CURDIR)/localrepo
	@echo $(CURDIR)/../../../../../RPMS
	@echo $(REDHAT.ROOT)
	ln -s $(CURDIR)/../../../../../RPMS $(CURDIR)/localrepo 
	createrepo -v $(CURDIR)/localrepo
	@echo -e "[localdir] \n\
name=local \n\
baseurl=file://$(CURDIR)/localrepo\n\
assumeyes=1 \n\
gpgcheck=0 \n\
enabled=1" > localdir.repo

getpackages:
	rm -rf cache
	mkdir -p cache
	zypper --pkg-cache-dir cache --reposd-dir $(CURDIR) clean --all
	$(info PATH is $(shell pwd))
	zypper --pkg-cache-dir cache --reposd-dir $(CURDIR) download $(YUMLIST)

