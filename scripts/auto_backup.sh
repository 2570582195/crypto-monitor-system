#!/bin/bash
# 自动化备份脚本 - 定期提交并推送代码到GitHub

echo "🔄 开始自动备份..."

# 切换到项目目录
cd D:/工作文件 || exit 1

# 检查是否有变更
if [[ -n $(git status --porcelain) ]]; then
    echo "📝 检测到代码变更，开始提交..."
    
    # 添加所有变更
    git add .
    
    # 生成提交信息（包含时间戳）
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    COMMIT_MSG="chore(auto-backup): 自动备份 ${TIMESTAMP}

- 自动提交未保存的变更
- 防止代码丢失"
    
    # 提交变更
    git commit -m "${COMMIT_MSG}"
    
    # 推送到远程仓库
    echo "📤 推送到GitHub..."
    git push origin main
    
    echo "✅ 备份完成！"
else
    echo "✨ 没有检测到变更，跳过备份。"
fi
