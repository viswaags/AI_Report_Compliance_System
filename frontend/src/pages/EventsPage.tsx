import { useEffect, useMemo, useState } from 'react';
import { Calendar, CalendarDays, Plus } from 'lucide-react';
import { StatusBadge } from '@/components/StatusBadge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useCurrentUser } from '@/hooks/useAuth';
import { useMyClubs } from '@/hooks/useClubs';
import { useCreateEvent, useEventCategories, useEvents, useMyEvents } from '@/hooks/useEvents';
import { toast } from 'sonner';

type BackendEvent = {
  id: number;
  club_id: number;
  event_title: string;
  event_category?: string | null;
  event_date?: string | null;
  status?: string | null;
};

type BackendClub = {
  id: number;
  club_name: string;
  description?: string | null;
};

type BackendUser = {
  id: number;
  name: string;
  email: string;
  role: 'ADMIN' | 'CLUB_COORDINATOR' | 'FACULTY_REPRESENTATIVE' | 'STUDENT_REPRESENTATIVE';
  is_active: boolean;
};

type EventForm = {
  club_id: string;
  event_title: string;
  event_category: string;
  event_date: string;
};

const emptyForm: EventForm = {
  club_id: '',
  event_title: '',
  event_category: '',
  event_date: '',
};

function formatDate(value?: string | null) {
  if (!value) return 'Unavailable';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString();
}

function formatStatus(value?: string | null) {
  return value ? value.toUpperCase() : '';
}

function EventTable({
  events,
  clubs,
  isLoading,
}: {
  events: BackendEvent[];
  clubs: BackendClub[];
  isLoading: boolean;
}) {
  const clubNames = useMemo(
    () => new Map(clubs.map((club) => [club.id, club.club_name])),
    [clubs]
  );

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Event Title</TableHead>
          <TableHead>Event Category</TableHead>
          <TableHead>Event Date</TableHead>
          <TableHead>Club</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {isLoading ? (
          <TableRow>
            <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
              Loading events...
            </TableCell>
          </TableRow>
        ) : events.length === 0 ? (
          <TableRow>
            <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
              No events available
            </TableCell>
          </TableRow>
        ) : (
          events.map((event) => (
            <TableRow key={event.id}>
              <TableCell>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <Calendar className="h-5 w-5 text-primary" />
                  </div>
                  <span className="font-medium">{event.event_title}</span>
                </div>
              </TableCell>
              <TableCell>
                {event.event_category ? (
                  <Badge variant="secondary">{event.event_category}</Badge>
                ) : (
                  <span className="text-muted-foreground">Unavailable</span>
                )}
              </TableCell>
              <TableCell>{formatDate(event.event_date)}</TableCell>
              <TableCell>{clubNames.get(event.club_id) ?? 'Unavailable'}</TableCell>
              <TableCell>
                {event.status ? (
                  <StatusBadge status={formatStatus(event.status)} />
                ) : (
                  <span className="text-muted-foreground">Unavailable</span>
                )}
              </TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  );
}

export function EventsPage() {
  const [form, setForm] = useState<EventForm>(emptyForm);
  const currentUserQuery = useCurrentUser();
  const eventsQuery = useEvents();
  const myEventsQuery = useMyEvents();
  const myClubsQuery = useMyClubs();
  const categoriesQuery = useEventCategories();
  const createEvent = useCreateEvent();

  const user = currentUserQuery.data as BackendUser | undefined;
  const allEvents = useMemo(
    () => (Array.isArray(eventsQuery.data) ? (eventsQuery.data as BackendEvent[]) : []),
    [eventsQuery.data]
  );
  const myEvents = useMemo(
    () => (Array.isArray(myEventsQuery.data) ? (myEventsQuery.data as BackendEvent[]) : []),
    [myEventsQuery.data]
  );
  const myClubs = useMemo(
    () => (Array.isArray(myClubsQuery.data) ? (myClubsQuery.data as BackendClub[]) : []),
    [myClubsQuery.data]
  );
  const categories = useMemo(
    () => (Array.isArray(categoriesQuery.data) ? (categoriesQuery.data as string[]) : []),
    [categoriesQuery.data]
  );
  const canCreateEvent = user?.role === 'STUDENT_REPRESENTATIVE';

  useEffect(() => {
    if (myClubs.length === 1 && form.club_id !== String(myClubs[0].id)) {
      setForm((current) => ({ ...current, club_id: String(myClubs[0].id) }));
    }
  }, [form.club_id, myClubs]);

  const updateForm = (key: keyof EventForm, value: string) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const handleCreateEvent = () => {
    if (!form.club_id || !form.event_title.trim()) return;

    createEvent.mutate(
      {
        club_id: Number(form.club_id),
        event_title: form.event_title.trim(),
        event_category: form.event_category || undefined,
        event_date: form.event_date || undefined,
      },
      {
        onSuccess: () => {
          setForm({
            ...emptyForm,
            club_id: myClubs.length === 1 ? String(myClubs[0].id) : '',
          });
          toast.success('Event created successfully.');
        },
        onError: () => {
          toast.error('Unable to create event.');
        },
      }
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Events</h1>
          <p className="text-muted-foreground">Manage club events and activities</p>
        </div>
      </div>

      <Tabs defaultValue="all" className="space-y-4">
        <TabsList className="flex-wrap">
          <TabsTrigger value="all">All Events</TabsTrigger>
          <TabsTrigger value="my">My Events</TabsTrigger>
          {canCreateEvent && (
            <TabsTrigger value="create">
              <CalendarDays className="mr-2 h-4 w-4" />
              Create Event
            </TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="all">
          <Card>
            <CardHeader>
              <CardTitle>Event List</CardTitle>
              <CardDescription>Events available from the backend</CardDescription>
            </CardHeader>
            <CardContent>
              {eventsQuery.isError ? (
                <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  Unable to load events.
                </p>
              ) : (
                <EventTable events={allEvents} clubs={myClubs} isLoading={eventsQuery.isLoading} />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="my">
          <Card>
            <CardHeader>
              <CardTitle>My Events</CardTitle>
              <CardDescription>Events associated with your clubs</CardDescription>
            </CardHeader>
            <CardContent>
              {myEventsQuery.isError ? (
                <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  Unable to load your events.
                </p>
              ) : (
                <EventTable events={myEvents} clubs={myClubs} isLoading={myEventsQuery.isLoading} />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {canCreateEvent && (
          <TabsContent value="create">
            <Card>
              <CardHeader>
                <CardTitle>Create New Event</CardTitle>
                <CardDescription>Schedule a new event for one of your clubs</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Club</label>
                    <Select
                      value={form.club_id}
                      onValueChange={(value) => updateForm('club_id', value)}
                      disabled={myClubsQuery.isLoading || myClubs.length === 1}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder={myClubsQuery.isLoading ? 'Loading clubs...' : 'Select club'} />
                      </SelectTrigger>
                      <SelectContent>
                        {myClubs.map((club) => (
                          <SelectItem key={club.id} value={String(club.id)}>
                            {club.club_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Event Title</label>
                    <Input
                      value={form.event_title}
                      onChange={(event) => updateForm('event_title', event.target.value)}
                      placeholder="Enter event title"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Event Category</label>
                    {categories.length > 0 ? (
                      <Select
                        value={form.event_category}
                        onValueChange={(value) => updateForm('event_category', value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select category" />
                        </SelectTrigger>
                        <SelectContent>
                          {categories.map((category) => (
                            <SelectItem key={category} value={category}>
                              {category}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    ) : (
                      <Input
                        value={form.event_category}
                        onChange={(event) => updateForm('event_category', event.target.value)}
                        placeholder="Enter event category"
                      />
                    )}
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Event Date</label>
                    <Input
                      type="date"
                      value={form.event_date}
                      onChange={(event) => updateForm('event_date', event.target.value)}
                    />
                  </div>
                </div>

                {myClubsQuery.isError && (
                  <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                    Unable to load your clubs.
                  </p>
                )}

                {createEvent.isError && (
                  <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                    Unable to create event.
                  </p>
                )}

                <div className="flex justify-end">
                  <Button
                    disabled={!form.club_id || !form.event_title.trim() || createEvent.isPending}
                    onClick={handleCreateEvent}
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    {createEvent.isPending ? 'Creating...' : 'Create Event'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}

export default EventsPage;
