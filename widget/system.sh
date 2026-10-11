#!/bin/bash
cpu=$(ps -A -o %cpu | awk '{s+=$1} END {printf "%.0f", s/'"$(sysctl -n hw.ncpu)"'}')
pg=$(sysctl -n hw.pagesize); tot=$(sysctl -n hw.memsize)
used=$(vm_stat | awk -v pg=$pg '/Pages active|Pages wired|Pages occupied by compressor/ {gsub("\\.","",$NF); s+=$NF} END {printf "%.0f", s*pg}')
mem=$(( used*100/tot ))
disk=$(df -h / | awk 'NR==2 {print $5}' | tr -d %)
bat=$(pmset -g batt | grep -Eo '[0-9]+%' | head -1 | tr -d %)
echo "{\"cpu\":${cpu:-0},\"mem\":${mem:-0},\"disk\":${disk:-0},\"bat\":${bat:-null}}"
