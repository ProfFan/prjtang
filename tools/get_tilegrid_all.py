#!/usr/bin/env python3
"""
For each architecture and part, obtain a tilegrid and save it in the database
"""

import os
from os import path
import shutil

import database
import tangdinasty
import json

def prepare_tcl(file_loc, out_file, part, package):
	with open(file_loc, "rt") as fin:
		with open(out_file, "wt") as fout:
			for line in fin:
				line = line.replace('{part}', part)
				line = line.replace('{package}', package)
				fout.write(line)

def prepare_pnl(architecture, part, package, max_row, max_col):
	tiles = ''
	for x in range(max_col):
		for y in range(max_row):
			tiles += '          x{}y{}_n1end0.x{}y{}_n1beg0\n'.format(x,y,x,y)      
	file_loc = path.join(database.get_tang_root(), "minitests", "tilegrid", "wire.pnl")
	with open(file_loc, "rt") as fin:
		with open("work_tilegrid/wire.pnl", "wt") as fout:
			for line in fin:
				line = line.replace('{architecture}', architecture)
				line = line.replace('{part}', part)
				line = line.replace('{package}', package)
				line = line.replace('{tiles}', tiles)
				fout.write(line)

def extract_elements(infile, tiles, max_row):
	with open(infile, "rt") as fin:
		for line in fin:				
			if (line.startswith('//')):
				inst = line.split(':')[1].split(',')[0]
				type = line.split('type=')[1].split(',')[0]
				wl_beg = line.split('wl_beg=')[1].split(',')[0]
				bl_beg = line.split('bl_beg=')[1].split(',')[0].rstrip('\n')
				loc = inst.split('_')[-1]
				val = loc.split('y')
				x = int(val[0].lstrip('x'))
				y = max_row - 1 - int(val[1])
				current_tile = {
					"x": x,
					"y": y,
					"loc": loc,
					"val": []
				}
				if (tiles[y][x]==0):
					tiles[y][x] = current_tile
				current_item = {
					"inst": inst,
					"type": type,
					"wl_beg": int(wl_beg),
					"bl_beg": int(bl_beg)
				}
				found = False
				for item in tiles[y][x]["val"]:
					if(item["inst"]==inst):
						found = True
				if found==False:
					tiles[y][x]["val"].append(current_item)
	
def extract_fuses(infile, architecture, part):
	frames = 0
	bits_per_frame = 0
	with open(infile, "rt") as fin:
		for line in fin:
			frames = frames + 1
			bits_per_frame = len(line.strip())
	data = {}
	data["frames"] = frames
	data["bits"] = bits_per_frame
	output_file = path.join(database.get_db_subdir(architecture, part), "fuses.json")
	with open(output_file, "wt") as fout:
		json.dump(data, fout, sort_keys=True, indent=4)


def main():
	devices = database.get_devices()
	for architecture in devices["architectures"].keys():
		for part in devices["architectures"][architecture]["parts"].keys():
			shutil.rmtree("work_tilegrid", ignore_errors=True)
			os.mkdir("work_tilegrid")
			selected_part = devices["architectures"][architecture]["parts"][part]
			package = selected_part["packages"][0]

			max_row = int(selected_part["max_row"])
			max_col = int(selected_part["max_col"])

			prepare_tcl(path.join(database.get_tang_root(), "minitests", "tilegrid", "wire.tcl"), "work_tilegrid/wire.tcl", part, package)
			prepare_pnl(architecture, part, package, max_row, max_col)
			tangdinasty.run("wire.tcl", "work_tilegrid")
			tiles = [[0 for y in range(max_col)] for x in range(max_row)] 
			extract_elements("work_tilegrid/wire.log", tiles, max_row)
			
			file_loc = path.join(database.get_tang_root(), "minitests", "tilegrid", part + ".v")
			if os.path.exists(file_loc):
				shutil.copyfile(file_loc,path.join("work_tilegrid", part + ".v"))
				prepare_tcl(path.join(database.get_tang_root(), "minitests", "tilegrid", "specific.tcl"), "work_tilegrid/specific.tcl", part, package)
				tangdinasty.run("specific.tcl", "work_tilegrid")
				extract_elements("work_tilegrid/" + part + ".log", tiles, max_row)

			output_file = path.join(database.get_db_subdir(architecture, part), "tilegrid.json")
			with open(output_file, "wt") as fout:
				json.dump(tiles, fout, sort_keys=True, indent=4)
			extract_fuses("work_tilegrid/wire.fuse", architecture, part)

if __name__ == "__main__":
	main()