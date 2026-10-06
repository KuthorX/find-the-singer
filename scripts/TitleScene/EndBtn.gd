extends Button

func _ready() -> void:
	# Quitting is not possible from a browser tab, so the button is desktop-only.
	visible = not OS.has_feature("web")

func _on_pressed() -> void:
	get_tree().quit()
