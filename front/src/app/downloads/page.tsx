import AppHeader from '@/widgets/header/header'
import Aside from '@/widgets/aside/aside'
import Content from '@/features/downloads/content/content'

export default function Downloads() {
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
