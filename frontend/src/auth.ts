import { queryOptions } from "@tanstack/react-query";

import { getCurrentUser } from "./api/client";

export const currentUserQuery = queryOptions({
  queryKey: ["current-user"],
  queryFn: getCurrentUser,
  retry: false,
  staleTime: 30_000,
});
