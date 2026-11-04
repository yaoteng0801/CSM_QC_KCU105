CXX ?= g++
CXXFLAGS ?= -O3 -std=c++17 -Wall -Wextra -Wpedantic
LDLIBS ?= -lpcap

.PHONY: all clean

all: minidaq_capture ethernet_frame_io

minidaq_capture: minidaq_capture.cpp isolated_hits.h
	$(CXX) $(CXXFLAGS) $< -o $@ $(LDLIBS)

ethernet_frame_io: ethernet_frame_io.cpp
	$(CXX) $(CXXFLAGS) $< -o $@ $(LDLIBS)

clean:
	rm -f minidaq_capture ethernet_frame_io
