# DCS Mission Time Splitter

Takes your mission file and spits out 3 version of it with different start times.

Requires Python 3. 

Usage:
```
python mts.py my_miz_file.miz
```

This does the following:

1. Creates a temporary directory (.tmp) in the current directory.
2. Creates a new directory with the same name as your mission.
3. Expands the miz file into that directory.
4. Re-writes the `mission` file with the first start time (morning time by default: 0630).
5. Re-archives the mission file into a new miz file (`my_miz_file-morning.miz`) and moves it into the directory created in step 2.
6. Repeats steps 4-5 with 'midday' and 'evening' (1230 and 1930 respectively)
7. Deletes the temporary directory.

In the case of `my_miz_file.miz` being the mission file. You'll end up with the following directory structure

```
<root>
    |
    - my_miz_file.miz
    - my_miz_file (Directory)
       |
       - my_miz_file-morning.miz
       - my_miz_file-midday.miz
       - my_miz_file-evening,miz
```

You can specify multiple miz files as arguments, and it will do the above steps for each miz file separately (finish with one, delete the tmp directory, then start the next).

# Default Times
By default the program will create 3 versions of the mission you provide it.
```python
times = {
    'morning': 23400,  # 06:30
    'midday': 45000,  # 12:30
    'evening': 70200  # 19:30
}
```
This is a key-value map at the beginning of the file. The keys represent the value added to the filename, and the values are starting times from midnight in seconds. Feel free to edit / add to / remove from these values if you'd like to in your own runnings. The defaults may change without notice on this repository.