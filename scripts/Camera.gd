extends Camera2D

enum CameraMode {
	FULL_FOLLOW,  # x 和 y 都平移
	X_ONLY,       # 只 x 平移，y 固定
	Y_ONLY,       # 只 y 平移，x 固定
	FIXED,        # 都不平移
	STEPPED       # 步进式（阈值）移动，可指定轴
}

# 玩家节点
@export var target: Node2D  # 拖拽玩家节点到此属性
# 地图边界
@export var map_min_x: float = 0.0
@export var map_max_x: float = 3000.0
@export var map_min_y: float = 0.0
@export var map_max_y: float = 3000.0
# 平滑速度（x轴和y轴平滑移动时使用）
@export var smooth_speed: float = 5.0
# y轴高度阈值（每隔多少像素触发一次y轴移动）
@export var height_threshold: float = 200.0
# 相机y轴的当前目标高度
var target_y: float = 0.0

func _ready():
	# 确保相机在游戏开始时启用
	make_current()
	# 初始化相机位置，确保一开始对齐玩家
	if target:
		global_position = target.global_position
		# 设置初始y轴目标高度
		target_y = global_position.y

func _process(delta):
	if target:
		# 获取玩家位置
		var target_position = target.global_position
		
		# 获取视口大小（考虑缩放）
		var viewport_size = get_viewport_rect().size / zoom
		var camera_extents = viewport_size / 2.0
		
		# x轴：平滑跟随玩家
		var new_position_x = target_position.x
		new_position_x = clamp(new_position_x, map_min_x + camera_extents.x, map_max_x - camera_extents.x)
		
		# y轴：只有当玩家跨越高度阈值时更新目标y位置
		var player_y = target_position.y
		var current_height_level = floor(target_y / height_threshold)
		var player_height_level = floor(player_y / height_threshold)
		
		if player_height_level != current_height_level:
			# 玩家跨越了高度阈值，更新目标y位置
			print("player_height_level updated", player_height_level)
			target_y = player_height_level * height_threshold
		
		# 限制y轴位置在地图边界内
		var new_position_y = clamp(target_y, map_min_y + camera_extents.y, map_max_y - camera_extents.y)
		
		# 平滑移动到新位置
		global_position = global_position.lerp(Vector2(new_position_x, new_position_y), smooth_speed * delta)
