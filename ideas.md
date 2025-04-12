Add a feature in the library to quickly jolt down some ideas for a new book


Use a Markdown front matter for metadata about the scenes
https://www.honeybadger.io/blog/python-markdown/

https://www.accessiblepublishing.ca/common-epub-issues/

Move the data back end from YAML to TTL
Could be convenient to query for links from any starting node
https://gitlab.gnome.org/GNOME/tinysparql/
https://gnome.pages.gitlab.gnome.org/tinysparql/method.SparqlConnection.update_resource.html
https://gnome.pages.gitlab.gnome.org/tinysparql/examples.html

```python
file = Gio.File.new_for_path(f'{self._base_directory}/test')
logger.info(file.get_path())

try:
    connection = Tsparql.SparqlConnection.new(
        Tsparql.SparqlConnectionFlags.NONE,
        file,
        Tsparql.sparql_get_ontology_nepomuk(),
        None)
    logger.info(connection)

    stmt = connection.query_statement(
            'SELECT DISTINCT ?s  WHERE { ' +
            '  ?s a nmm:MusicPiece ' +
            '}', None)

    cursor = stmt.execute()
    i = 0;

    while cursor.next():
        i += 1
        print('Result {0}: {1}'.format(i, cursor.get_string(0)[0]))

    # Create a resource containing RDF data
    resource = Tsparql.Resource.new(None)
    resource.set_uri('rdf:type', 'nmm:MusicPiece')

    # Create a batch, and add the resource to it
    batch = connection.create_batch()
    batch.add_resource(None, resource)

    # Execute the batch to insert the data
    res = batch.execute()
    logger.info(res)

    connection.close()
except Exception as e:
    logger.error('Error: {0}'.format(e))
```
