import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {
  title: '那个夏天 · frank 小世界',
  description: 'Frank 制作的哆啦A梦同人 3D 小镇。走进大雄家，使用竹蜻蜓和任意门，过桥去后山，体验四季与昼夜。欢迎一起共建。',
  authors: [{name: 'Frank', url: 'https://github.com/frankfanyiming/frank_worlds'}],
};
export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) {
  return <html lang="zh-CN"><body>{children}</body></html>;
}
