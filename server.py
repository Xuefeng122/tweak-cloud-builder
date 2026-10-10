#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Tweak Cloud Builder")

BUILD_DIR = Path("./builds")
BUILD_DIR.mkdir(exist_ok=True)

TWEAK_TEMPLATE = '''#import <UIKit/UIKit.h>
#import <Foundation/Foundation.h>

@interface UpdateAlertManager : NSObject
+ (instancetype)shared;
- (void)checkUpdate;
@end

@implementation UpdateAlertManager

+ (instancetype)shared {
    static UpdateAlertManager *instance;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        instance = [[self alloc] init];
    });
    return instance;
}

- (void)checkUpdate {
    NSString *currentVersion = [[[NSBundle mainBundle] infoDictionary] objectForKey:@"CFBundleShortVersionString"];
    NSString *lastVersion = [[NSUserDefaults standardUserDefaults] stringForKey:@"LastAppVersion"];

    if (lastVersion && [currentVersion isEqualToString:lastVersion]) {
        return;
    }

    dispatch_async(dispatch_get_main_queue(), ^{
        UIWindowScene *scene = (UIWindowScene *)[[UIApplication sharedApplication].connectedScenes anyObject];
        UIViewController *topVC = scene.windows.firstObject.rootViewController;

        while (topVC.presentedViewController) {
            topVC = topVC.presentedViewController;
        }

        NSString *message;
        if (lastVersion) {
            message = [NSString stringWithFormat:@"{{UPDATE_MSG}}", lastVersion, currentVersion];
        } else {
            message = [NSString stringWithFormat:@"{{FIRST_MSG}}", currentVersion];
        }

        UIAlertController *alert = [UIAlertController alertControllerWithTitle:@"{{TITLE}}"
                                                                       message:message
                                                                preferredStyle:UIAlertControllerStyleAlert];
        [alert addAction:[UIAlertAction actionWithTitle:@"知道了" style:UIAlertActionStyleDefault handler:nil]];

        [topVC presentViewController:alert animated:YES completion:nil];
    });

    [[NSUserDefaults standardUserDefaults] setObject:currentVersion forKey:@"LastAppVersion"];
    [[NSUserDefaults standardUserDefaults] synchronize];
}

@end

%hook UIApplication

- (void)applicationDidBecomeActive:(UIApplication *)application {
    %orig;
    [[UpdateAlertManager shared] checkUpdate];
}

%end
'''

MAKEFILE_TEMPLATE = '''TARGET := iphone:clang:latest:14.0
INSTALL_TARGET_PROCESSES = {{PROCESS_NAME}}

include $(THEOS)/makefiles/common.mk

TWEAK_NAME = {{TWEAK_NAME}}

{{TWEAK_NAME}}_FILES = Tweak.x
{{TWEAK_NAME}}_CFLAGS = -fobjc-arc

include $(THEOS_MAKE_PATH)/tweak.mk
'''

PLIST_TEMPLATE = '''{
    "Filter": {
        "Bundles": ["{{BUNDLE_ID}}"]
    }
}
'''


class BuildRequest(BaseModel):
    bundle_id: str
    process_name: str
    tweak_name: str = "UpdateAlertTweak"
    alert_title: str = "更新提示"
    alert_message_update: str = "已从 v%@ 更新到 v%@"
    alert_message_first: str = "欢迎使用 v%@"


@app.post("/build")
def build(req: BuildRequest):
    work_dir = BUILD_DIR / req.tweak_name
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)

    # 生成 Tweak.x
    tweak_code = TWEAK_TEMPLATE
    tweak_code = tweak_code.replace("{{TITLE}}", req.alert_title)
    tweak_code = tweak_code.replace("{{UPDATE_MSG}}", req.alert_message_update)
    tweak_code = tweak_code.replace("{{FIRST_MSG}}", req.alert_message_first)
    (work_dir / "Tweak.x").write_text(tweak_code, encoding="utf-8")

    # 生成 Makefile
    makefile = MAKEFILE_TEMPLATE
    makefile = makefile.replace("{{PROCESS_NAME}}", req.process_name)
    makefile = makefile.replace("{{TWEAK_NAME}}", req.tweak_name)
    (work_dir / "Makefile").write_text(makefile, encoding="utf-8")

    # 生成 plist
    plist = PLIST_TEMPLATE
    plist = plist.replace("{{BUNDLE_ID}}", req.bundle_id)
    (work_dir / f"{req.tweak_name}.plist").write_text(plist, encoding="utf-8")

    # 编译
    result = subprocess.run(
        ["make", "package"],
        cwd=work_dir,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"编译失败: {result.stderr}")

    # 找 deb 文件
    packages_dir = work_dir / "packages"
    debs = list(packages_dir.glob("*.deb"))
    if not debs:
        raise HTTPException(status_code=500, detail="编译成功但没找到 deb 文件")

    deb_name = debs[0].name
    return {
        "success": True,
        "download_url": f"/download/{deb_name}",
        "tweak_name": req.tweak_name,
    }


@app.get("/download/{filename}")
def download(filename: str):
    # 防止路径穿越
    if "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="非法文件名")

    # 遍历所有 build 目录找文件
    for build_dir in BUILD_DIR.iterdir():
        deb_path = build_dir / "packages" / filename
        if deb_path.exists():
            return FileResponse(deb_path, filename=filename)

    raise HTTPException(status_code=404, detail="文件不存在")


@app.get("/")
def home():
    return {
        "name": "Tweak Cloud Builder",
        "status": "running",
        "endpoint": "POST /build",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
