import type { Metadata } from 'next';
import './globals.css';
import './xlands.css';
export const metadata: Metadata = {
  title: '小世界 · XLands',
  description: '进入小世界，旅行、探索，也留下自己的作品。',
  authors: [{name: 'Frank', url: 'https://github.com/frankfanyiming/frank_worlds'}],
};
export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) {
  return <html lang="zh-CN"><body>{children}</body></html>;
}
