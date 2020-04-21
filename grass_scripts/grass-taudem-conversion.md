# Converting GRASS r.watershed results for use with TauDEM

Before doing any of the following, set the computational region to match the
 input raster.

```python
gscript.run_command('g.region', raster=imported_dem)
```


## Drainage Direction to P


| dir | GRASS | TauDEM |
| --- | -----:| ------:|
| E   |     8 |      1 |
| NE  |     1 |      2 |
| N   |     2 |      3 |
| NW  |     3 |      4 |
| W   |     4 |      5 |
| SW  |     5 |      6 |
| S   |     6 |      7 |
| SE  |     7 |      8 |

```python
expr = "{o} = if({i}=>1, if({i}==8, 1, {i} + 1), null())".format(o=output, i=input)
```

## Stream segments to SRC

- nodata = 0
- Anything else = 1

```python
expr = "{o} = if(isnull({i}), 0, 1)".format(o=output, i=input)
```

## Export file settings

- format: GTiff
- type: Int16
- create options: COMPRESS=LZW,PREDICTOR=2,BIGTIFF=YES