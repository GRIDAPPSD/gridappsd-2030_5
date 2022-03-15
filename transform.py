from pathlib import Path

for line in Path("/repos/gridappsd-2030_5/ieee_2030_5/models/device_category.py").read_text().split("\n"):
    fields = line.split()
    try:
        int_data = int(fields[1])
        value = fields[3:]
        print(f"{'_'.join([x.upper().replace('.', '_').replace('(', '_').replace(')', '_') for x in value])} = {int_data}")
    except ValueError:
        print(line)
    except IndexError:
        pass
