# falcon-i18n

## Localization

- Init local
```
pybabel init -D mgo -i locale/mgo.pot -d locale -l uk
```

- Extract messages
```
pybabel extract -F babel.ini --sort-output --project=mgo -o locale/mgo.pot .
```

- Compile messages
```
pybabel compile -D mgo -d locale -i locale/uk/LC_MESSAGES/mgo.po --o locale/uk/LC_MESSAGES/mgo.mo
```

- Update catalog for certain locale
```
pybabel update -D mgo -i locale/mgo.pot -d locale -l uk
```

[Command-Line Interface for babel](http://babel.pocoo.org/en/latest/cmdline.html)


## Monkey-patching of default behavior of falcon
```
def to_json(self):
    obj = self.to_dict(OrderedDict)
    return json.dumps(
        obj, cls=JSONEncoder, ensure_ascii=False, indent=4,
        separators=(',', ': ')
    )


falcon.HTTPError.to_json = to_json
```
