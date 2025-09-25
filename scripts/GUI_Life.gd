extends Label

func _ready():
	# 连接到GameState的信号
	if has_node("/root/GameState"):
		var game_state = get_node("/root/GameState")
		game_state.connect("health_changed", Callable(self, "_on_health_changed"))
		
		# 初始化显示
		text = str(game_state.current_health)
	else:
		push_error("GameState not found. Make sure it's properly set as an autoload.")
		text = "0"

func _on_health_changed(current_health, max_health):
	# 更新Label显示的文本
	text = str(current_health)
