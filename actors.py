import datetime
from dapr.actor import ActorInterface, Actor, Remindable, actormethod
from models import Banner
from dapr.clients import DaprClient
from typing import Optional

BANNER_DURATION_SECONDS = 60

# This interface is used by the ActorProxy to call methods on the actor.
class BannerActorInterface(ActorInterface):
    @actormethod(name="UpdateState")
    async def update_state(self, data: Banner) -> Banner:
        ...

    @actormethod(name="GetState")
    async def get_state(self) -> Banner:
        ...
    
# Define an actor that represents a message banner
class BannerActor(Actor, BannerActorInterface, Remindable):
    async def _on_activate(self) -> None:
        # Load state on activation
        print(f'~~ Activate {self.__class__.__name__} {self.id}!', flush=True)

        # This provides a default state of an empty banner if state is missing
        # Note that model_dump is used to convert banner state to a dict which dapr can serialize as it passes it around
        state = await self._state_manager.get_or_add_state('banner', Banner(id=self.id.id).model_dump())
        self.banner = Banner.model_validate(state)
        await self.create_clear_reminder()

    async def process_state_change(self):
        # Save new state to state store
        # Note that model_dump is used to transmit state as a serializable dict
        await self._state_manager.set_state('banner', self.banner.model_dump())

        # Publish an event with the update
        with DaprClient() as client:
            client.publish_event(
                pubsub_name='pubsub',
                topic_name='banner_updated',
                data=self.banner.model_dump_json(),
                data_content_type='application/json',
            )

        await self.create_clear_reminder()

    async def create_clear_reminder(self):
        # If a message was set, create a reminder to clear it after BANNER_DURATION_SECONDS seconds
        if self.banner.message != "":
            await self.register_reminder(
                'clear',
                b'clear', # No payload, throws error if left empty so repeating event name
                datetime.timedelta(seconds=BANNER_DURATION_SECONDS),
                datetime.timedelta(seconds=BANNER_DURATION_SECONDS),
                datetime.timedelta(seconds=BANNER_DURATION_SECONDS)
            )

    async def update_state(self, update):
        # Throw an error and prevent update if there is a current message
        if self.banner.message != "":
            raise ValueError('Banner already has a message. Please wait for it to expire.')

        # Update actor internal state
        self.banner = self.banner.model_copy(update=update)
        self.banner.expires = datetime.datetime.now() + datetime.timedelta(seconds=BANNER_DURATION_SECONDS)

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

