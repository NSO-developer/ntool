DIRS = internal

ifeq ($(BUILD_JOB),external)
DIR = external
endif

ifeq ($(BUILD_JOB),internal_realhw)
DIR = internal
JOB_DIR = realhw
endif

ifeq ($(BUILD_JOB),internal_simulated)
DIR = internal
JOB_DIR = simulated
endif

ifeq ($(BUILD_JOB),)
DIR = internal
JOB_DIR = simulated
endif

all: build test

clean:
	$(MAKE) -C $(DIR) clean JOB_DIR=$(JOB_DIR) || exit 1

test:
	$(MAKE) -C $(DIR) test JOB_DIR=$(JOB_DIR) || exit 1

build:
	$(MAKE) -C $(DIR) build JOB_DIR=$(JOB_DIR) || exit 1

desc:
	@echo "==Test Cases for external-id-allocation=="
	@for d in $(DIRS) ; do \
	  $(MAKE) -sC $$d desc || exit 1; \
	done
