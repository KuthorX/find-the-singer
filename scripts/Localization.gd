extends Node

# Chooses the UI language (Chinese or English), persists it and keeps the window title in sync.

const SETTINGS_PATH := "user://settings.cfg"
const SECTION := "general"
const KEY_LOCALE := "locale"
const SUPPORTED_LOCALES: Array[String] = ["zh", "en"]

func _ready() -> void:
	apply_locale(_load_saved_locale())

func get_current_locale() -> String:
	return TranslationServer.get_locale().substr(0, 2)

func toggle_locale() -> void:
	var next_locale := "en" if get_current_locale() == "zh" else "zh"
	apply_locale(next_locale)
	_save_locale(next_locale)

func apply_locale(locale: String) -> void:
	TranslationServer.set_locale(locale)
	get_window().title = tr("GAME_TITLE")

func _default_locale() -> String:
	return "zh" if OS.get_locale_language() == "zh" else "en"

func _load_saved_locale() -> String:
	var config := ConfigFile.new()
	if config.load(SETTINGS_PATH) != OK:
		return _default_locale()
	var saved: String = str(config.get_value(SECTION, KEY_LOCALE, ""))
	return saved if saved in SUPPORTED_LOCALES else _default_locale()

func _save_locale(locale: String) -> void:
	var config := ConfigFile.new()
	config.load(SETTINGS_PATH)
	config.set_value(SECTION, KEY_LOCALE, locale)
	var err := config.save(SETTINGS_PATH)
	if err != OK:
		push_warning("Could not save language setting (error %d)." % err)
