export type UserRole = 'ADMIN' | 'CLUB_COORDINATOR' | 'FACULTY_REPRESENTATIVE' | 'STUDENT_REPRESENTATIVE';

export type ReportStatus =
  | 'DRAFT'
  | 'VALIDATING'
  | 'COMPLIANCE_PASSED'
  | 'CORRECTION_REQUIRED'
  | 'REVISION_REQUIRED'
  | 'UNDER_REVIEW'
  | 'APPROVED'
  | 'REJECTED'
  | 'ARCHIVED';

export type NotificationStatus = 'READ' | 'UNREAD';

export type MembershipStatus = 'ACTIVE' | 'INACTIVE' | 'PENDING';

export type EventStatus = 'UPCOMING' | 'ONGOING' | 'COMPLETED' | 'CANCELLED';

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_by?: number | null;
  must_change_password: boolean;
  created_at?: string;
}

export interface Club {
  id: string;
  name: string;
  description: string;
  category: string;
  facultyAdvisorId?: string;
  coordinatorId?: string;
  status: MembershipStatus;
  memberCount: number;
  eventCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface Membership {
  id: string;
  userId: string;
  clubId: string;
  role: 'PRESIDENT' | 'VICE_PRESIDENT' | 'SECRETARY' | 'TREASURER' | 'MEMBER';
  status: MembershipStatus;
  joinedAt: string;
  user?: User;
  club?: Club;
}

export interface Event {
  id: string;
  clubId: string;
  title: string;
  description: string;
  type: 'WORKSHOP' | 'SEMINAR' | 'COMPETITION' | 'SOCIAL' | 'COMMUNITY_SERVICE' | 'OTHER';
  startDate: string;
  endDate: string;
  venue: string;
  status: EventStatus;
  expectedAttendees: number;
  actualAttendees?: number;
  reportRequired: boolean;
  reportSubmitted: boolean;
  createdAt: string;
  updatedAt: string;
  club?: Club;
}

export interface Report {
  id: string;
  eventId: string;
  submittedBy: string;
  status: ReportStatus;
  version: number;
  filePath: string;
  fileName: string;
  fileSize: number;
  validationResults?: ValidationResult[];
  feedback?: Feedback[];
  reviewHistory?: ReviewHistory[];
  submittedAt: string;
  updatedAt: string;
  event?: Event;
  submitter?: User;
}

export interface ValidationResult {
  id: string;
  reportId: string;
  field: string;
  status: 'PASS' | 'FAIL' | 'WARNING';
  message: string;
  expectedValue?: string;
  actualValue?: string;
}

export interface Feedback {
  id: string;
  reportId: string;
  userId: string;
  content: string;
  type: 'CORRECTION' | 'SUGGESTION' | 'APPROVAL';
  createdAt: string;
  user?: User;
}

export interface ReviewHistory {
  id: string;
  reportId: string;
  reviewerId: string;
  action: 'APPROVED' | 'REJECTED' | 'REQUESTED_REVISION';
  comment: string;
  createdAt: string;
  reviewer?: User;
}

export interface Template {
  id: string;
  name: string;
  description: string;
  version: string;
  filePath: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface RepositoryRecord {
  id: string;
  reportId: string;
  eventId: string;
  clubId: string;
  archivedAt: string;
  archivedBy: string;
  tags: string[];
  report?: Report;
  event?: Event;
  club?: Club;
}

export interface Notification {
  id: string;
  userId: string;
  title: string;
  message: string;
  type: 'REPORT_SUBMITTED' | 'VALIDATION_COMPLETE' | 'REVIEW_REQUEST' | 'APPROVAL' | 'REJECTION' | 'REVISION_REQUEST' | 'SYSTEM';
  status: NotificationStatus;
  link?: string;
  createdAt: string;
}

export interface DashboardStats {
  totalClubs: number;
  totalEvents: number;
  pendingReports: number;
  pendingReviews: number;
  reportsByStatus: Record<ReportStatus, number>;
  eventsByMonth: { month: string; count: number }[];
  reportsByClub: { club: string; count: number }[];
}
