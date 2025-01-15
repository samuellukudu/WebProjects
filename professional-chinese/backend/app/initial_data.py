initial_vocabulary = [
    # Meetings and Presentations
    {
        "chinese_simplified": "会议",
        "chinese_traditional": "會議",
        "pinyin": "huì yì",
        "english": "meeting",
        "context_category": "Meetings",
        "difficulty_level": 1,
        "usage_examples": {
            "example1": {
                "chinese": "我们下周有个重要会议。",
                "pinyin": "Wǒmen xià zhōu yǒu gè zhòngyào huìyì.",
                "english": "We have an important meeting next week."
            }
        }
    },
    {
        "chinese_simplified": "演示",
        "chinese_traditional": "演示",
        "pinyin": "yǎn shì",
        "english": "presentation",
        "context_category": "Meetings",
        "difficulty_level": 2,
        "usage_examples": {
            "example1": {
                "chinese": "请准备项目演示。",
                "pinyin": "Qǐng zhǔnbèi xiàngmù yǎnshì.",
                "english": "Please prepare the project presentation."
            }
        }
    },
    
    # Project Management
    {
        "chinese_simplified": "截止日期",
        "chinese_traditional": "截止日期",
        "pinyin": "jié zhǐ rì qī",
        "english": "deadline",
        "context_category": "Project Management",
        "difficulty_level": 2,
        "usage_examples": {
            "example1": {
                "chinese": "这个项目的截止日期是什么时候？",
                "pinyin": "Zhège xiàngmù de jiézhǐ rìqī shì shénme shíhòu?",
                "english": "What's the deadline for this project?"
            }
        }
    },
    {
        "chinese_simplified": "进度",
        "chinese_traditional": "進度",
        "pinyin": "jìn dù",
        "english": "progress",
        "context_category": "Project Management",
        "difficulty_level": 1,
        "usage_examples": {
            "example1": {
                "chinese": "请汇报项目进度。",
                "pinyin": "Qǐng huìbào xiàngmù jìndù.",
                "english": "Please report on the project progress."
            }
        }
    },
    
    # Email Communication
    {
        "chinese_simplified": "附件",
        "chinese_traditional": "附件",
        "pinyin": "fù jiàn",
        "english": "attachment",
        "context_category": "Email",
        "difficulty_level": 1,
        "usage_examples": {
            "example1": {
                "chinese": "我已经把报告作为附件发送给你了。",
                "pinyin": "Wǒ yǐjīng bǎ bàogào zuòwéi fùjiàn fāsòng gěi nǐ le.",
                "english": "I have sent you the report as an attachment."
            }
        }
    },
    {
        "chinese_simplified": "回复",
        "chinese_traditional": "回覆",
        "pinyin": "huí fù",
        "english": "reply",
        "context_category": "Email",
        "difficulty_level": 1,
        "usage_examples": {
            "example1": {
                "chinese": "请尽快回复这封邮件。",
                "pinyin": "Qǐng jǐnkuài huífù zhè fēng yóujiàn.",
                "english": "Please reply to this email as soon as possible."
            }
        }
    },
    
    # Technical Discussions
    {
        "chinese_simplified": "代码",
        "chinese_traditional": "代碼",
        "pinyin": "dài mǎ",
        "english": "code",
        "context_category": "Technical",
        "difficulty_level": 1,
        "usage_examples": {
            "example1": {
                "chinese": "这段代码需要优化。",
                "pinyin": "Zhè duàn dàimǎ xūyào yōuhuà.",
                "english": "This code needs optimization."
            }
        }
    },
    {
        "chinese_simplified": "调试",
        "chinese_traditional": "調試",
        "pinyin": "tiáo shì",
        "english": "debug",
        "context_category": "Technical",
        "difficulty_level": 2,
        "usage_examples": {
            "example1": {
                "chinese": "我正在调试这个问题。",
                "pinyin": "Wǒ zhèngzài tiáoshì zhège wèntí.",
                "english": "I am debugging this issue."
            }
        }
    },
    
    # HR/Administrative
    {
        "chinese_simplified": "请假",
        "chinese_traditional": "請假",
        "pinyin": "qǐng jià",
        "english": "request leave",
        "context_category": "HR",
        "difficulty_level": 1,
        "usage_examples": {
            "example1": {
                "chinese": "我想请假三天。",
                "pinyin": "Wǒ xiǎng qǐngjià sān tiān.",
                "english": "I would like to request three days of leave."
            }
        }
    },
    {
        "chinese_simplified": "加班",
        "chinese_traditional": "加班",
        "pinyin": "jiā bān",
        "english": "overtime work",
        "context_category": "HR",
        "difficulty_level": 1,
        "usage_examples": {
            "example1": {
                "chinese": "这周我们需要加班。",
                "pinyin": "Zhè zhōu wǒmen xūyào jiābān.",
                "english": "We need to work overtime this week."
            }
        }
    }
]

from sqlalchemy.orm import Session
from . import models

def seed_vocabulary(db: Session):
    for vocab in initial_vocabulary:
        db_vocab = models.Vocabulary(**vocab)
        db.add(db_vocab)
    try:
        db.commit()
        print("Successfully seeded vocabulary data")
    except Exception as e:
        print(f"Error seeding vocabulary data: {e}")
        db.rollback()
