extends Label

func _ready():
	# 连接到GameState的信号
	var game_state = get_node("/root/GameState")
	game_state.connect("letter_bonus_collected", Callable(self, "_on_letter_bonus_collected"))
	
	# 初始化显示
	text = "信件: 0"

func _on_letter_bonus_collected(total_count):
	# 更新Label显示的文本
	text = "信件: " + str(total_count)