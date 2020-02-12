# Nano pore data process
 python code to read nano pore readings

https://nanoporetech.com/
"When a nanopore is present in an electrically insulating membrane, it can be used as a single-molecule detector. It can be a biological protein channel in a high electrical resistance lipid bilayer, a pore in a solid-state membrane or a hybrid of these – a protein channel set in a synthetic membrane. The detection principle is based on monitoring the ionic current passing through the nanopore as a voltage is applied across the membrane. When the nanopore is of molecular dimensions, passage of molecules (e.g., DNA) cause interruptions of the "open" current level, leading to a "translocation event" signal. The passage of RNA or single-stranded DNA molecules through the membrane-embedded alpha-hemolysin channel (1.5 nm diameter), for example, causes a ~90% blockage of the current (measured at 1 M KCl solution)"

This code tries to read each channel (pore) and find the time window where a protein or DNA sequence continuously passing through.
