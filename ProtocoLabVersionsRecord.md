1.0.0.0 -
		Initial release of ProtocoLab.
1.0.1.0 -
		Added support of uploding a CSV as input.
1.0.1.1 -
		Added exit code 1 when CompareTool failes and fixed bug that MR name cannot contain period.
1.0.2.0 - 
		Added execution state column.
1.0.3.0 - 
		Add support for "run from selection" - user can now select certain rows to compare by using the checkboxes on the left.
		Add log folder to conatin all external tool logs and log name now contains MR name.
		Add log folder to contain all GUI logs and log file name is now ProtocoLab.
		Add "clean execution" before comparing - execution state restarts before every run.
		Add Open Latest Log - allows the user to open latest compare log.
		Add ability to make requirements from a given tar file.
		Add enriched log file of both GUI and external tool.
		Concatenate logs of runs that occured in less than 2 minutes one after another.
1.0.4.0 - 
		Add button "Select All" to select all rows in data grid.
		Add button "Unselect All" to unselect all rows in data grid.
		Cancel the ability to concatenate logs.
1.0.5.0 - 
		New macro.
		Responsive datagrid.
		"Break" button to halt comparison process.
		"Open Log" button to view a specific log, of one of the runs.
1.0.5.1 -
		SQAT-6 fix.
		SQAT-17 fix.
1.0.5.2 -
		Add remove_readonly function to extract_tar function, to remove read-only attribute if folder cannot be deleted.