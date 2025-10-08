import AppHeader from '@/widgets/header/header'
import Aside from '@/widgets/aside/aside'
import Content from '@/features/recs/content/content'

export default function Recs() {
  return (
    <>
      <AppHeader />
      <div className="flex container">
        <Aside />
        <Content />
      </div>
    </>
  );
}
