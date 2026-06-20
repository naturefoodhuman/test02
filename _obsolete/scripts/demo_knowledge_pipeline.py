# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间）：2026-06-15 12:00:00 CST
"""专家大脑建设演示脚本：河南区域知识注入流程

本脚本演示如何将一个‘河南地方法规’从抓取 $\rightarrow$ 审核 $\rightarrow$ 清洗 $\rightarrow$ 入库。
"""

from pathlib import Path
from _factory.knowledge_pipeline.pipeline import KnowledgePipeline
from _factory.knowledge_pipeline.schemas import DataSourceType, AuditStatus

def run_demo():
    root = Path(".").resolve()
    pipeline = KnowledgePipeline(root)
    
    print("🚀 开始执行知识注入流程: [河南地方法规-债务执行专项]...")
    
    # 1. Acquire: 模拟从河南高院抓取一段指南
    raw_content = "根据河南省高级人民法院关于执行工作的最新指南，对于涉及农村集体土地的债务争议，应优先协调乡镇政府介入..."
    source_url = "http://henan.court.gov.cn/guidelines/2026-execute-01"
    
    atom_id = pipeline.acquire(
        content=raw_content,
        source_url=source_url,
        source_type=DataSourceType.GUIDELINE,
        region="henan"
    )
    print(f"✅ [Acquire] 知识原子创建成功: {atom_id}")
    
    # 2. Audit: 模拟由法律专家进行审核
    is_approved = pipeline.audit(
        atom_id=atom_id,
        auditor_id="expert_lawyer_01",
        status=AuditStatus.APPROVED
    )
    print(f"✅ [Audit] 审核状态: {'通过' if is_approved else '拒绝'}")
    
    # 3. Clean: 模拟将冗长文本清洗为结构化 SOP
    cleaned_content = "【河南专项-农村债权执行】\n1. 优先级：乡镇政府协调 $\rightarrow$ 法院执行\n2. 核心要点：必须确认集体土地确权状态\n3. 风险：注意村民委员会的干扰因素"
    pipeline.clean(
        atom_id=atom_id,
        cleaned_content=cleaned_content,
        version="1.0"
    )
    print(f"✅ [Clean] 知识原子结构化完成")
    
    # 4. Ingest: 入库到债务律师专家大脑
    success = pipeline.ingest(
        atom_id=atom_id,
        expert_name="debt-lawyer"
    )
    print(f"✅ [Ingest] 知识成功注入 debt-lawyer 专家大脑: {success}")
    print(f"\n🏁 流程结束。你可以检查 _factory/experts/debt-lawyer.expert/knowledge/ 目录查看产物。")

if __name__ == "__main__":
    run_demo()
