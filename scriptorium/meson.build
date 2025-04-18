pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'scriptorium'
gnome = import('gnome')
python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
	input: 'scriptorium.in',
	output: 'scriptorium',
	configuration: conf,
	install: true,
	install_dir: get_option('bindir'),
	install_mode: 'r-xr-xr-x',
)

scriptorium_sources = [
	'__init__.py',
	'main.py',
	'window.py',
	'model.py',
	'utils.py',
	'globals.py',
	'editor/editor.py',
	'editor/editor_entity.py',
	'editor/editor_overview.py',
	'editor/editor_formatting.py',
	'editor/editor_writing.py',
	'editor/plotting.py',
	'editor/scene.py',
	'editor/chapter_column.py',
	'library/library.py',
	'library/manuscript.py',
	'editor/writer.py',
]

blueprints = custom_target(
	'blueprints',
	input: files(
		'editor/chapter_column.blp',
		'editor/editor.blp',
		'editor/editor_entity.blp',
		'editor/editor_formatting.blp',
		'editor/editor_overview.blp',
		'editor/editor_writing.blp',
		'editor/plotting.blp',
		'editor/scene.blp',
		'library/library.blp',
		'library/manuscript.blp',
		'window.blp',
		'editor/writer.blp',
	),
	output: '.',
	command: [
		find_program('blueprint-compiler'),
		'batch-compile',
		'@OUTPUT@',
		'@CURRENT_SOURCE_DIR@',
		'@INPUT@',
	],
)

gnome.compile_resources(
	'scriptorium',
	'scriptorium.gresource.xml',
	gresource_bundle: true,
	install: true,
	install_dir: pkgdatadir,
	dependencies: blueprints,
)

install_data(scriptorium_sources, install_dir: moduledir)
