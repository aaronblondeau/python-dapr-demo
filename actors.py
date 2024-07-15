import datetime
from dapr.actor import ActorInterface, Actor, Remindable, actormethod
from models import Banner
from dapr.clients import DaprClient
from typing import Optional

class BannerActorInterface(ActorInterface):
    @actormethod(name="UpdateState")
    async def update_state(self, data: Banner) -> Banner:
        ...

    @actormethod(name="GetState")
    async def get_state(self) -> Banner:
        ...
    
class BannerActor(Actor, BannerActorInterface, Remindable):
    async def _on_activate(self) -> None:
        print(f'~~ Activate {self.__class__.__name__} {self.id}!', flush=True)
        state = await self._state_manager.get_or_add_state('banner', Banner(id=self.id.id).model_dump())
        self.banner = Banner.model_validate(state)
        await self.create_clear_reminder()

    async def process_state_change(self):
        # Save new state to state store
        await self._state_manager.set_state('banner', self.banner.model_dump())

        # Publish an event with the update
        with DaprClient() as client:
            client.publish_event(
                pubsub_name='pubsub',
                topic_name='banner_updated', # self.id.id + '_banner',
                data=self.banner.model_dump_json(),
                data_content_type='application/json',
            )

        await self.create_clear_reminder()
        

    async def create_clear_reminder(self):
        # If a message was set, create a reminder to clear it after 60 seconds
        if self.banner.message != "":
            await self.register_reminder(
                'clear',
                b'clear', # No payload
                datetime.timedelta(seconds=60),
                datetime.timedelta(seconds=60),
                datetime.timedelta(seconds=60)
            )

    async def update_state(self, update):
        # Throw an error and prevent update if there is a current message
        if self.banner.message != "":
            raise ValueError('Banner already has a message. Please wait for it to expire.')

        # Update actor internal state
        self.banner = self.banner.model_copy(update=update)

        # Save and emit events
        await self.process_state_change()

        return self.banner.model_dump()

    async def get_state(self) -> Banner:
        return self.banner.model_dump()
    
    async def receive_reminder(
        self,
        name: str,
        state: bytes,
        due_time: datetime.timedelta,
        period: datetime.timedelta,
        ttl: Optional[datetime.timedelta] = None,
    ) -> None:
        print(f'~~ receive_reminder : {name} - {str(state)}', flush=True)
        if name == 'clear':
            # Clear Banner
            self.banner = Banner(id=self.id.id)

            # Save and emit events
            await self.process_state_change()

