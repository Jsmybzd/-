-- ============================================
-- 修复脚本：解决登录问题和区域表问题
-- ============================================
USE NationalParkDB;
GO

-- ============================================
-- 1. 修复登录问题：为所有用户设置默认密码
--    默认密码: 123456
--    SHA256哈希: 8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92
-- ============================================
PRINT N'正在修复用户密码...';

-- 检查密码哈希列是否存在
IF COL_LENGTH(N'用户', N'密码哈希') IS NULL
BEGIN
    ALTER TABLE [用户] ADD [密码哈希] NVARCHAR(64) NULL;
    PRINT N'已添加密码哈希列';
END

-- 为所有用户设置默认密码（包括张三 13800000007）
UPDATE [用户] 
SET [密码哈希] = '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92'
WHERE [密码哈希] IS NULL OR [密码哈希] = '' OR phone = '13800000007';

PRINT N'已为所有用户设置默认密码 (123456)';
GO

-- ============================================
-- 2. 检查并修复区域表结构
-- ============================================
PRINT N'正在检查区域表结构...';

-- 检查区域表是否存在必要的列
IF OBJECT_ID(N'区域表', N'U') IS NOT NULL
BEGIN
    -- 添加缺失的列（如果不存在）
    IF COL_LENGTH(N'区域表', N'lng') IS NULL AND COL_LENGTH(N'区域表', N'longitude') IS NULL
    BEGIN
        ALTER TABLE 区域表 ADD lng FLOAT NULL;
        PRINT N'已添加 lng 列';
    END
    
    IF COL_LENGTH(N'区域表', N'lat') IS NULL AND COL_LENGTH(N'区域表', N'latitude') IS NULL
    BEGIN
        ALTER TABLE 区域表 ADD lat FLOAT NULL;
        PRINT N'已添加 lat 列';
    END
    
    PRINT N'区域表结构检查完成';
END
GO

-- ============================================
-- 3. 显示当前用户列表（验证修复结果）
-- ============================================
PRINT N'';
PRINT N'===== 当前用户列表 =====';
SELECT id, name, phone, role_type, 
       CASE WHEN [密码哈希] IS NOT NULL AND [密码哈希] <> '' THEN N'已设置' ELSE N'未设置' END AS [密码状态]
FROM [用户];

PRINT N'';
PRINT N'===== 区域表结构 =====';
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = N'区域表';

PRINT N'';
PRINT N'修复完成！现在可以使用以下账号登录：';
PRINT N'手机号: 13800000005';
PRINT N'密码: 123456';
GO
