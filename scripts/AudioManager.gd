extends Node

# Owns every sound in the game: the Music / SFX buses, the saved volume and
# mute settings, the music of each screen and a small pool of SFX voices.
#
# "The unfinished song": the gameplay track is five synced stems. The base
# band always plays; the melody stems join as the level's letters are found,
# so the song fills in while you collect them (docs/audio-direction.md).

signal settings_changed
signal sfx_played(sfx_name: String)
signal music_changed(track: String)

const SETTINGS_PATH := "user://settings.cfg"
const SECTION := "audio"
const BUS_MASTER := &"Master"
const BUS_MUSIC := &"Music"
const BUS_SFX := &"SFX"
const DEFAULT_MUSIC_VOLUME := 0.7
const DEFAULT_SFX_VOLUME := 0.8
const SILENT_DB := -60.0
const FADE_IN_SECONDS := 0.8
const FADE_OUT_SECONDS := 0.4
const TIER_FADE_SECONDS := 1.5
const SAVE_DELAY_SECONDS := 0.5
const SFX_VOICES := 10
const UI_QUIET_MS := 250
const UI_REPEAT_MS := 70
const FAR_DISTANCE := 1600.0
const WEB_PRELOAD_GAP_SECONDS := 0.4
# Share of the level's letters needed before each melody stem joins (mel1 is always on).
const TIER_THRESHOLDS: Array[float] = [0.0, 0.3, 0.6, 0.9]
# Letter pickups climb the D-major pentatonic, ending on the top D at the 11th letter.
const LETTER_STEPS: Array[int] = [-12, -10, -8, -5, -3, 0, 2, 4, 7, 9, 12]
const UI_PRESS_SOUNDS := {
	"StartBtn": "ui_confirm", "RetryBtn": "ui_confirm",
	"BackToMenuBtn": "ui_back", "ExitBtn": "ui_back",
	"LanguageBtn": "ui_toggle", "MuteBtn": "ui_toggle",
}

const MUSIC_MENU: AudioStream = preload("res://audio/music/menu.mp3")
const MUSIC_STEMS: Array[AudioStream] = [
	preload("res://audio/music/play_base.mp3"),
	preload("res://audio/music/play_mel1.mp3"),
	preload("res://audio/music/play_mel2.mp3"),
	preload("res://audio/music/play_mel3.mp3"),
	preload("res://audio/music/play_mel4.mp3"),
]
const JINGLES := {
	"complete": preload("res://audio/sfx/jingle_complete.mp3"),
	"gameover": preload("res://audio/sfx/jingle_gameover.mp3"),
}
const SFX := {
	"jump": preload("res://audio/sfx/jump.wav"),
	"land_measure": preload("res://audio/sfx/land_measure.wav"),
	"land_fragile": preload("res://audio/sfx/land_fragile.wav"),
	"land_repeat": preload("res://audio/sfx/land_repeat.wav"),
	"land_gliss": preload("res://audio/sfx/land_gliss.wav"),
	"bounce": preload("res://audio/sfx/bounce.wav"),
	"fragile_crack": preload("res://audio/sfx/fragile_crack.wav"),
	"fragile_break": preload("res://audio/sfx/fragile_break.wav"),
	"fragile_restore": preload("res://audio/sfx/fragile_restore.wav"),
	"letter": preload("res://audio/sfx/letter.wav"),
	"checkpoint": preload("res://audio/sfx/checkpoint.wav"),
	"hurt": preload("res://audio/sfx/hurt.wav"),
	"respawn": preload("res://audio/sfx/respawn.wav"),
	"life_up": preload("res://audio/sfx/life_up.wav"),
	"ui_hover": preload("res://audio/sfx/ui_hover.wav"),
	"ui_click": preload("res://audio/sfx/ui_click.wav"),
	"ui_confirm": preload("res://audio/sfx/ui_confirm.wav"),
	"ui_back": preload("res://audio/sfx/ui_back.wav"),
	"ui_toggle": preload("res://audio/sfx/ui_toggle.wav"),
}

var music_volume := DEFAULT_MUSIC_VOLUME
var sfx_volume := DEFAULT_SFX_VOLUME
var muted := false
var current_track := ""

var _menu_player: AudioStreamPlayer
var _jingle_player: AudioStreamPlayer
var _stem_players: Array[AudioStreamPlayer] = []
var _sfx_players: Array[AudioStreamPlayer] = []
var _next_voice := 0
var _fades := {}
var _scene: Node = null
var _letters_total := 0
var _tiers_on := 0
var _last_max_health := 0
var _ui_quiet_until := 0
var _last_ui_sound := 0
var _save_pending := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_load_settings()
	_apply_bus_volumes()
	_menu_player = _make_player(BUS_MUSIC, MUSIC_MENU)
	_jingle_player = _make_player(BUS_MUSIC, null)
	_jingle_player.finished.connect(_on_jingle_finished)
	for stem in MUSIC_STEMS:
		_stem_players.append(_make_player(BUS_MUSIC, stem))
	for i in SFX_VOICES:
		_sfx_players.append(_make_player(BUS_SFX, null))
	get_tree().node_added.connect(_on_node_added)
	GameState.letter_bonus_collected.connect(_on_letter_collected)
	GameState.health_changed.connect(_on_health_changed)
	_last_max_health = GameState.max_health
	if OS.has_feature("web"):
		_preload_web_samples()


func _process(_delta: float) -> void:
	var scene := get_tree().current_scene
	if scene != _scene:
		_scene = scene
		if scene != null:
			_on_scene_changed(scene.scene_file_path)


func _unhandled_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key != null and key.pressed and not key.echo and key.physical_keycode == KEY_M:
		toggle_mute()
		get_viewport().set_input_as_handled()


## Web builds play audio as Web Audio samples that are decoded on first play.
## Decode the gameplay stems while the title screen is up so Start does not stall.
func _preload_web_samples() -> void:
	var streams: Array = MUSIC_STEMS + JINGLES.values()
	for stream: AudioStream in streams:
		await get_tree().create_timer(WEB_PRELOAD_GAP_SECONDS).timeout
		if not AudioServer.is_stream_registered_as_sample(stream):
			AudioServer.register_stream_as_sample(stream)


# ---------------------------------------------------------------- SFX API

func play_sfx(sfx_name: String, volume_db := 0.0, pitch := 1.0) -> void:
	var stream: AudioStream = SFX.get(sfx_name)
	if stream == null:
		push_warning("Unknown sound effect: %s" % sfx_name)
		return
	var player := _sfx_players[_next_voice]
	_next_voice = (_next_voice + 1) % _sfx_players.size()
	player.stream = stream
	player.volume_db = volume_db
	player.pitch_scale = pitch
	player.play()
	sfx_played.emit(sfx_name)


## Plays a world sound quieter the further it is from the camera centre.
func play_sfx_at(sfx_name: String, world_position: Vector2) -> void:
	var camera := get_viewport().get_camera_2d()
	if camera == null:
		play_sfx(sfx_name)
		return
	var distance := camera.get_screen_center_position().distance_to(world_position)
	var gain := clampf(1.0 - distance / FAR_DISTANCE, 0.0, 1.0)
	if gain > 0.0:
		play_sfx(sfx_name, linear_to_db(gain))


func play_sfx_later(sfx_name: String, delay_seconds: float) -> void:
	get_tree().create_timer(delay_seconds).timeout.connect(play_sfx.bind(sfx_name))


# ---------------------------------------------------------------- settings API

func set_music_volume(value: float) -> void:
	music_volume = clampf(value, 0.0, 1.0)
	_settings_updated()


func set_sfx_volume(value: float) -> void:
	sfx_volume = clampf(value, 0.0, 1.0)
	_settings_updated()


func set_muted(value: bool) -> void:
	muted = value
	_settings_updated()


func toggle_mute() -> void:
	set_muted(not muted)
	play_sfx("ui_toggle")


func _settings_updated() -> void:
	_apply_bus_volumes()
	_queue_save()
	settings_changed.emit()


func _apply_bus_volumes() -> void:
	_set_bus(BUS_MASTER, 1.0, muted)
	_set_bus(BUS_MUSIC, music_volume, false)
	_set_bus(BUS_SFX, sfx_volume, false)


func _set_bus(bus_name: StringName, linear: float, mute: bool) -> void:
	var index := AudioServer.get_bus_index(bus_name)
	if index < 0:
		push_error("Audio bus '%s' is missing from default_bus_layout.tres." % bus_name)
		return
	AudioServer.set_bus_volume_db(index, linear_to_db(maxf(linear, 0.0001)))
	AudioServer.set_bus_mute(index, mute or linear <= 0.001)


func _load_settings() -> void:
	var config := ConfigFile.new()
	if config.load(SETTINGS_PATH) != OK:
		return
	music_volume = clampf(float(config.get_value(SECTION, "music_volume", DEFAULT_MUSIC_VOLUME)), 0.0, 1.0)
	sfx_volume = clampf(float(config.get_value(SECTION, "sfx_volume", DEFAULT_SFX_VOLUME)), 0.0, 1.0)
	muted = bool(config.get_value(SECTION, "muted", false))


func _queue_save() -> void:
	if _save_pending:
		return
	_save_pending = true
	get_tree().create_timer(SAVE_DELAY_SECONDS).timeout.connect(_save_settings)


func _save_settings() -> void:
	_save_pending = false
	var config := ConfigFile.new()
	config.load(SETTINGS_PATH)  # keep the other sections (language)
	config.set_value(SECTION, "music_volume", music_volume)
	config.set_value(SECTION, "sfx_volume", sfx_volume)
	config.set_value(SECTION, "muted", muted)
	var err := config.save(SETTINGS_PATH)
	if err != OK:
		push_warning("Could not save audio settings (error %d)." % err)


# ---------------------------------------------------------------- music

func _on_scene_changed(path: String) -> void:
	if path.ends_with("TitleScene.tscn"):
		_play_menu()
	elif path.get_file().begins_with("Level_"):
		_play_gameplay()
	elif path.ends_with("FinishLevel.tscn"):
		_play_jingle("complete")
	elif path.ends_with("GameOver.tscn"):
		_play_jingle("gameover")


func _play_menu() -> void:
	if current_track == "menu":
		return
	_set_track("menu")
	_stop_gameplay()
	_menu_player.volume_db = SILENT_DB
	_menu_player.play()
	_fade(_menu_player, 0.0, FADE_IN_SECONDS)


func _play_gameplay() -> void:
	_set_track("gameplay")
	_fade(_menu_player, SILENT_DB, FADE_OUT_SECONDS, true)
	_jingle_player.stop()
	_letters_total = get_tree().get_nodes_in_group("letters").size()
	_tiers_on = _tiers_for(GameState.letter_bonus_count)
	# All stems start on the same frame so they stay locked together.
	for i in _stem_players.size():
		var player := _stem_players[i]
		_kill_fade(player)
		player.volume_db = 0.0 if i <= _tiers_on else SILENT_DB
		player.play()


func _play_jingle(jingle: String) -> void:
	_set_track("jingle")
	_stop_gameplay()
	_fade(_menu_player, SILENT_DB, FADE_OUT_SECONDS, true)
	_jingle_player.stream = JINGLES[jingle]
	_jingle_player.volume_db = 0.0
	_jingle_player.play()


func _on_jingle_finished() -> void:
	if current_track == "jingle":
		_play_menu()


func _stop_gameplay() -> void:
	for player in _stem_players:
		if player.playing:
			_fade(player, SILENT_DB, FADE_OUT_SECONDS, true)


func _set_track(track: String) -> void:
	current_track = track
	music_changed.emit(track)


func _tiers_for(letters: int) -> int:
	if _letters_total == 0:
		return TIER_THRESHOLDS.size()
	var tiers := 0
	for threshold in TIER_THRESHOLDS:
		if letters >= ceili(threshold * _letters_total):
			tiers += 1
	return tiers


func _update_tiers(letters: int) -> void:
	if current_track != "gameplay":
		return
	var tiers := _tiers_for(letters)
	if tiers == _tiers_on:
		return
	_tiers_on = tiers
	for i in range(1, _stem_players.size()):
		_fade(_stem_players[i], 0.0 if i <= tiers else SILENT_DB, TIER_FADE_SECONDS)


func _fade(player: AudioStreamPlayer, to_db: float, seconds: float, stop_after := false) -> void:
	_kill_fade(player)
	var tween := create_tween()
	tween.tween_property(player, "volume_db", to_db, seconds)
	if stop_after:
		tween.tween_callback(player.stop)
	_fades[player] = tween


func _kill_fade(player: AudioStreamPlayer) -> void:
	var tween: Tween = _fades.get(player)
	if tween != null and tween.is_valid():
		tween.kill()
	_fades.erase(player)


# ---------------------------------------------------------------- game events

func _on_letter_collected(total_count: int) -> void:
	var step: int = LETTER_STEPS[(total_count - 1) % LETTER_STEPS.size()]
	play_sfx("letter", 0.0, pow(2.0, step / 12.0))
	_update_tiers(total_count)


func _on_health_changed(_current_health: int, max_health: int) -> void:
	if max_health > _last_max_health:
		play_sfx("life_up")
	_last_max_health = max_health


# ---------------------------------------------------------------- UI sounds

func _on_node_added(node: Node) -> void:
	var button := node as BaseButton
	if button == null:
		return
	# Buttons grab focus as their screen opens; that should not make a sound.
	_ui_quiet_until = Time.get_ticks_msec() + UI_QUIET_MS
	button.mouse_entered.connect(_on_ui_hover.bind(button))
	button.focus_entered.connect(_on_ui_hover.bind(button))
	button.pressed.connect(_on_ui_pressed.bind(button))


func _on_ui_hover(button: BaseButton) -> void:
	var now := Time.get_ticks_msec()
	if button.disabled or now < _ui_quiet_until or now - _last_ui_sound < UI_REPEAT_MS:
		return
	_last_ui_sound = now
	play_sfx("ui_hover")


func _on_ui_pressed(button: BaseButton) -> void:
	_last_ui_sound = Time.get_ticks_msec()
	play_sfx(UI_PRESS_SOUNDS.get(String(button.name), "ui_click"))


func _make_player(bus: StringName, stream: AudioStream) -> AudioStreamPlayer:
	var player := AudioStreamPlayer.new()
	player.bus = bus
	player.stream = stream
	add_child(player)
	return player
