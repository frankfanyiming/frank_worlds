import { cloneElement, isValidElement, type ReactNode, type ReactElement } from 'react';
import type { Locale } from '../community/i18n';
import translations from './ui-translations.json';
import traditional from './ui-traditional.json';
const dictionary = translations as Record<string, string[]>;
const zhTitles: Record<string,string> = {'A POCKET FULL OF WONDERS':'口袋里的小惊喜','AFTER SCHOOL CLUB':'放学后的伙伴','THE TIME MACHINE':'时光机'};
const pick = (locale:Locale, en:string, ja:string, ko:string, cn:string, tw:string) => ({en,ja,ko,'zh-CN':cn,'zh-TW':tw})[locale];

/** Translate at the render boundary. Engine state stays unchanged: interaction routing
 * still uses its source IDs/text, and changing locale never overwrites a saved message. */
export function townText(locale:Locale, source:string):string {
 const key=source.trim().replace(/\s+/g,' ');
 if(!key)return source;
 if(locale==='zh-CN')return zhTitles[key] ?? source;
 if(locale==='zh-TW' && (traditional as Record<string,string>)[key]) return (traditional as Record<string,string>)[key];
 const row=dictionary[key];
 if(row && locale!=='zh-TW')return row[{en:0,ja:1,ko:2}[locale]];
 const t=(s:string)=>townText(locale,s);
 let m:RegExpMatchArray|null;
 if((m=key.match(/^(春|夏|秋|冬)日 · (夜色|晴空)$/)))return `${t(m[1])} · ${t(m[2])}`;
 if((m=key.match(/^和(.+)聊聊$/)))return pick(locale,`Talk to ${t(m[1])}`,`${t(m[1])}と話す`,`${t(m[1])}와 대화`,'',`和${t(m[1])}聊聊`);
 if((m=key.match(/^任意门通往(.+)，走进门或点击“穿过任意门”。$/)))return t('任意门通往')+t(m[1])+t('，走进门或点击“穿过任意门”。');
 if((m=key.match(/^任意门已抵达：(.+)$/)))return t('任意门已抵达：')+t(m[1]);
 if((m=key.match(/^挑战结束 · 命中 (\d+) 次，个人最佳 (\d+) 次。$/)))return t('挑战结束 · 命中')+m[1]+t('次，个人最佳')+m[2]+t('次。');
 if((m=key.match(/^时光旅行抵达：(.+)。走下楼看看小镇的变化吧。$/)))return t('时光旅行抵达：')+t(m[1])+t('。走下楼看看小镇的变化吧。');
 if((m=key.match(/^一起散步 (\d+) \/ 25 米$/)))return t('一起散步')+m[1]+t('/ 25 米');
 if((m=key.match(/^第 (\d+) \/ 5 球 · 命中 (\d+)$/)))return pick(locale,`Pitch ${m[1]} / 5 · Hits ${m[2]}`,`${m[1]} / 5 球 · 命中 ${m[2]}`,`${m[1]} / 5구 · 명중 ${m[2]}`,'',`第 ${m[1]} / 5 球 · 命中 ${m[2]}`);
 if((m=key.match(/^还剩 (\d+) 秒 · 命中 (\d+)$/)))return pick(locale,`${m[1]} s left · Hits ${m[2]}`,`残り ${m[1]} 秒 · 命中 ${m[2]}`,`${m[1]}초 남음 · 명중 ${m[2]}`,'',`還剩 ${m[1]} 秒 · 命中 ${m[2]}`);
 if((m=key.match(/^(.+)超时，请检查网络后重试。$/)))return pick(locale,`${t(m[1])} timed out. Check your connection and retry.`,`${t(m[1])}がタイムアウトしました。接続を確認して再試行してください。`,`${t(m[1])} 시간 초과. 연결을 확인하고 다시 시도해요.`,'',`${t(m[1])}逾時，請檢查網路後重試。`);
 if((m=key.match(/^资源请求失败（(\d+)）$/)))return pick(locale,`Resource request failed (${m[1]})`,`リソースの取得に失敗 (${m[1]})`,`리소스 요청 실패 (${m[1]})`,'',`資源請求失敗（${m[1]}）`);
 // Preserve imported filenames and other user-authored text; never translate by substring.
 return source;
}

/** The JSX tree contains computed text too (dialogue, status, scores and descriptions).
 * Clone only presentation children/labels, never callbacks, values, IDs or world data. */
export function localizeTownUI(node:ReactNode, locale:Locale):ReactNode {
 if(typeof node==='string')return townText(locale,node);
 if(Array.isArray(node))return node.map(child=>localizeTownUI(child,locale));
 if(!isValidElement(node))return node;
 const el=node as ReactElement<Record<string,unknown>>;
 if(el.props['data-no-translate'])return node;
 const props:Record<string,unknown>={};
 for(const key of ['title','aria-label','alt','placeholder','closeLabel'])if(typeof el.props[key]==='string')props[key]=townText(locale,el.props[key] as string);
 if(el.props.children!==undefined)props.children=localizeTownUI(el.props.children as ReactNode,locale);
 return cloneElement(el,props);
}
