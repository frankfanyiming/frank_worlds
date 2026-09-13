export const CREATOR = {
  x: 'https://x.com/FrankFYM001',
  douyin: 'frank001',
  xiaohongshu: '150015050',
  xiaohongshuUrl: 'https://www.xiaohongshu.com/user/profile/55d96ee558944639c3ce03f1',
  makingOf: 'https://xgenlabs.feishu.cn/docx/EHsmd08qGo3T7nxWKIMchlcGnvb',
};

// Clipboard writes only happen after an explicit button click.
export async function copyPlainText(text: string) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}
