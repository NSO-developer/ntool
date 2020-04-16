all: fxs
.PHONY: all

# Include standard NCS examples build definitions and rules
include $(NCS_DIR)/src/ncs/build/include.ncs.mk

SRC = $(wildcard yang/*.yang)
DIRS = ../load-dir java/src/$(JDIR)/$(NS)
FXS = $(SRC:yang/%.yang=../load-dir/%.fxs)

## Uncomment and patch the line below if you have a dependency to a NED
## or to other YANG files
# YANGPATH += ../../<ned-name>/src/ncsc-out/modules/yang \
# 	../../<pkt-name>/src/yang

NCSCPATH   = $(YANGPATH:%=--yangpath %)
YANGERPATH = $(YANGPATH:%=--path %)

fxs: $(DIRS) $(FXS)

$(DIRS):
	mkdir -p $@

../load-dir/%.fxs: yang/%.yang ../ntool_modules/ntool_template.py ../ntool_modules/ntool_verify.py
	$(NCSC)  `ls $*-ann.yang  > /dev/null 2>&1 && echo "-a $*-ann.yang"` \
             $(NCSCPATH) -c -o $@ $<
	@echo "Copying template to python directory"
	cp ../ntool_modules/ntool_template.py ../python/
	@echo "Copying ntool_template.py and ntool_verify to ../scripts/command"
	cp ../ntool_modules/ntool_template.py ../scripts/command/
	chmod 755 ../scripts/command/ntool_template.py
	cp ../ntool_modules/ntool_verify.py ../scripts/command/
	chmod 755 ../scripts/command/ntool_verify.py
	

clean:
	rm -rf $(DIRS)
	rm -rf ../scripts/command/*.py
	rm -rf ../python/ntool_template.py
.PHONY: clean
