extends HBoxContainer

# Title-screen sound controls: music / effects volume and mute (also on the M key).

const TICK_INTERVAL_MS := 90
const MUTED_ALPHA := 0.4

@onready var _music_slider: HSlider = $MusicSlider
@onready var _sfx_slider: HSlider = $SfxSlider
@onready var _mute_btn: Button = $MuteBtn

var _last_tick := 0


func _ready() -> void:
	_music_slider.set_value_no_signal(AudioManager.music_volume)
	_sfx_slider.set_value_no_signal(AudioManager.sfx_volume)
	_music_slider.value_changed.connect(_on_music_changed)
	_sfx_slider.value_changed.connect(_on_sfx_changed)
	_mute_btn.pressed.connect(_on_mute_pressed)
	AudioManager.settings_changed.connect(_refresh)
	_refresh()


func _notification(what: int) -> void:
	if what == NOTIFICATION_TRANSLATION_CHANGED and is_node_ready():
		_refresh()


func _on_music_changed(value: float) -> void:
	AudioManager.set_music_volume(value)


func _on_sfx_changed(value: float) -> void:
	AudioManager.set_sfx_volume(value)
	# Let the player hear the new effects level while dragging.
	var now := Time.get_ticks_msec()
	if now - _last_tick >= TICK_INTERVAL_MS:
		_last_tick = now
		AudioManager.play_sfx("ui_toggle")


func _on_mute_pressed() -> void:
	AudioManager.set_muted(not AudioManager.muted)


func _refresh() -> void:
	_mute_btn.text = tr("AUDIO_UNMUTE") if AudioManager.muted else tr("AUDIO_MUTE")
	_music_slider.editable = not AudioManager.muted
	_sfx_slider.editable = not AudioManager.muted
	for control: Control in [$MusicLabel, _music_slider, $SfxLabel, _sfx_slider]:
		control.modulate.a = MUTED_ALPHA if AudioManager.muted else 1.0
