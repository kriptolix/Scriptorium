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
	'application.py',
	'window.py',
	'utils.py',
	'globals.py',
	'language_tool.py',
]
install_data(scriptorium_sources, install_dir: moduledir)


blueprints = custom_target(
	'blueprints',
	input: files(
		'window.blp',

		'dialogs/dialog_add.blp',
		'dialogs/writer.blp',
		'dialogs/select_scenes.blp',
		'dialogs/select_entities.blp',

		'views/library.blp',
		'views/editor.blp',
		'views/editor_overview.blp',
		'views/editor_chapters.blp',
		'views/editor_chapters_details.blp',
		'views/editor_scenes.blp',
		'views/editor_scenes_details.blp',
		'views/editor_formatting.blp',
		'views/editor_manuscript.blp',
		'views/editor_entities.blp',
		'views/editor_entities_details.blp',

		'widgets/chapter_column.blp',
		'widgets/scene.blp',
		'widgets/chapter.blp',
		'widgets/entity_card.blp',
		'widgets/manuscript.blp',
		'widgets/multiline_entry_row.blp',
		'widgets/cards_list.blp',
		'widgets/theme_selector.blp',
		'widgets/annotation.blp',
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

subdir('models')
subdir('dialogs')
subdir('widgets')
subdir('views')


