#!/usr/bin/env python3

import sys
import os
import json

IRQ_CHIP_PREFIX="IR-PCI-MSIX-"

# Function to parse /proc/interrupts and extract interrupt counts for each CPU and each interrupt
def get_irq_counts(n_cpus, pci): 

    irq_dict = {}

    irq_chip = IRQ_CHIP_PREFIX + pci

    with open('/proc/interrupts', 'r') as f:
        for line in f:
            if irq_chip in line:
                # Split the line into key and interrupt counts
                fields = line.strip().split()
                virq = fields[0].split(':')[0]       # Virtual IRQ
                hwirq = fields[-2].split('-')[0]     # Get the hwirq as the key
                i_counts = [int(count) for count in fields[1:n_cpus+1]] 
                key = f"{hwirq} {virq}"
                irq_dict[key] = i_counts
    
    return irq_dict

def save_irq_counts(irq_dict, fname):
    with open(fname, 'w') as f:
        json.dump(irq_dict, f)

def load_irq_counts(fname):
    with open(fname, 'r') as f:
        irq_dict = json.load(f)

    return irq_dict

def diff_irq_counts(new, old):
   diff = {}
   for key in new:
       d_counts = [ x - y for x, y in zip(new[key], old[key])]
       diff[key] = d_counts

   return diff


SFILE=".m_irqs.start"
EFILE=".m_irqs.end"

def main():
    
    start = False
    end = False
    compress = False

    pci_addr = sys.argv[1]
    
    for i in range(2, len(sys.argv)):
        if sys.argv[i] == "--compress":
            compress = True
        elif sys.argv[i] == '--start':
            start = True
        elif sys.argv[i] == '--end':
            end = True 
        elif sys.argv[i] == '--print':
            pass 
        else:
            print("Usage: m_irqs.py <pci_addr> --start|--end [tmpfile]") 
            sys.exit(1)

    n_cpus = os.cpu_count()
    if start:
        irq_counts = get_irq_counts(n_cpus, pci_addr)
        save_irq_counts(irq_counts, SFILE)
        print("Saved IRQ counts in ", SFILE)
        sys.exit(0)

    if end:
        irq_counts = get_irq_counts(n_cpus, pci_addr)
        save_irq_counts(irq_counts, EFILE)
    else:
        irq_counts = load_irq_counts(EFILE)


    old_irq_counts = load_irq_counts(SFILE)

    diff_counts = diff_irq_counts(irq_counts, old_irq_counts)

    print("HW(VIRQ)  Diff")
    for key in diff_counts:
        t_count = sum(diff_counts[key])
        irqs = key.split()
        if not compress or t_count != 0:
            print("{:<7} {:>6}".format(f"{irqs[0]}({irqs[1]})", sum(diff_counts[key])))


    cpu_diffs = [0] * n_cpus
    for key in diff_counts:
        irq_diffs = diff_counts[key]
        for cpu in range(n_cpus):
            cpu_diffs[cpu] += irq_diffs[cpu]

    print("\nCPU    Diff")
    for cpu in range(n_cpus):
        if not compress or cpu_diffs[cpu] != 0:
            print("{:<4} {:>6}".format(cpu, cpu_diffs[cpu]))


if __name__ == "__main__":
    # execute only if run as a script
    main()

